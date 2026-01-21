import json, os
from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from src.tools.openai_chat.client import OpenAIClient
from src.tools.anthropic_chat.client import AnthropicClient

from src.tools.auth import User, require_active_user
from src.utils.settings_utils import UserSettingsService
from src.utils.conversation_utils import ConversationService, MessageService
from src.utils.conversation_utils.summary_helper import ConversationSummaryHelper
from src.utils.memory_utils import MemoryService
from src.utils.conversation_state_utils import ConversationStateService
from src.utils.conversation_project_utils import ConversationProjectService
from src.data.model_capabilities import get_capabilities, get_provider
from src.data.instructions import Instructions
from src.tools.state.state_handler import StateHandler
from src.api.dependencies import get_openai_message_handler, get_anthropic_message_handler


router = APIRouter()


def get_project_instructions(project_id: int, user_id: int) -> str | None:
    """
    Fetch project custom instructions if project exists and user has access.
    Returns None if no project_id, project not found, or no custom instructions.
    """
    if not project_id:
        return None
    
    project = ConversationProjectService.get_project(project_id, user_id)
    if project and project.custom_instructions:
        return project.custom_instructions
    return None


def link_conversation_to_project(conversation_id: int, project_id: int, user_id: int) -> None:
    """
    Link a new conversation to a project. Fails silently on error.
    """
    if not project_id or not conversation_id:
        return
    
    try:
        ConversationProjectService.add_conversation(conversation_id, project_id, user_id)
    except Exception as e:
        # Log but don't fail the chat - linking is secondary to chat functionality
        print(f"[chat] Failed to link conversation {conversation_id} to project {project_id}: {e}")


@router.get("/chat")
async def chat(message: str, model: str = None,
               provider: str = None, conversation_id: int = None,
               project_id: int = None,
               user: User = Depends(require_active_user),
               anthropic_message_handler=Depends(get_anthropic_message_handler),
               openai_message_handler=Depends(get_openai_message_handler)):
    """
    Send a chat message.

    Args:
        message: The user's message
        model: Model to use (optional - falls back to user's default)
        provider: Provider to use (optional - falls back to user's default)
        conversation_id: Conversation to continue (optional - creates new if not provided)
        project_id: Project context (optional - applies custom instructions, links new convos)
        user: Current user

    Resolution order for model/provider:
    - If model provided without provider: infer provider from model name
    - If provider provided without model: use user's default model for that provider
    - If neither provided: use user's default settings
    - If both provided: use as-is

    Returns:
        response: The assistant's reply
        conversation_id: The conversation ID (new or existing)
    """
    try:
        # =================================================================
        # Step 1: Resolve provider and model from user settings
        # =================================================================
        settings = UserSettingsService.get_settings(user.id)

        if model and not provider:
            provider = get_provider(model)
            if not provider:
                provider = settings.provider

        elif provider and not model:
            model = settings.default_model

        elif not provider and not model:
            provider = settings.provider
            model = settings.default_model

        # =================================================================
        # Step 1b: Get model capabilities and user preferences
        # =================================================================
        capabilities = get_capabilities(model)
        enable_thinking = (
                capabilities.reasoning_type == "extended_thinking"
                and settings.enable_extended_thinking
        )
        thinking_budget = settings.anthropic_thinking_budget

        # =================================================================
        # Step 1c: Get project instructions if project context provided
        # =================================================================
        project_instructions = get_project_instructions(project_id, user.id)

        # =================================================================
        # Step 2: Get or create conversation
        # =================================================================
        is_new_conversation = False
        if conversation_id:
            # Verify ownership
            conversation = ConversationService.get_conversation(conversation_id, user.id)
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Auto-create new conversation
            is_new_conversation = True
            conversation = ConversationService.create_conversation(
                user.id,
                title="New Conversation"
            )
            conversation_id = conversation.id
            
            # Link to project if project_id provided
            if project_id:
                link_conversation_to_project(conversation_id, project_id, user.id)

        # =================================================================
        # Step 2b: Load or create conversation state
        # =================================================================
        saved_state = ConversationStateService.get_state(conversation_id)
        if saved_state:
            state_handler = StateHandler.from_dict(conversation_id, saved_state)
        else:
            state_handler = StateHandler(conversation_id)

        state_handler.update_state_from_message(message)

        # =================================================================
        # Step 3: Save user message to database
        # =================================================================
        MessageService.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            model=model,
            provider=provider,
            tokens_used=None,  # We don't track input tokens currently
            user_id=user.id
        )

        # =================================================================
        # Step 4: Get response from LLM
        # =================================================================
        memories = MemoryService.get_memories(user.id, limit=settings.memory_limit)
        memories_text = MemoryService.format_for_prompt(memories)

        state = state_handler.get_state()
        state["conversation_id"] = conversation_id  # Add for recent exchanges lookup
        instructions_text = Instructions(
            state, 
            user=user, 
            memories_text=memories_text,
            project_instructions=project_instructions
        ).build_instructions()
        tool_context = {"user_id": user.id, "user_role": user.role, "user_specialties": user.specialty_roles, "conversation_id": conversation_id}

        thinking_content = None
        if provider == "anthropic":
            response, thinking_content = anthropic_message_handler.handle_message(
                instructions=instructions_text,
                message=message,
                model=model,
                enable_thinking=enable_thinking,
                thinking_budget=thinking_budget,
                tool_context=tool_context
            )
        else:
            response = openai_message_handler.handle_message(
                instructions=instructions_text,
                message=message,
                model=model,
                tool_context=tool_context
            )

        # =================================================================
        # Step 5: Save assistant message to database
        # =================================================================
        assistant_message = MessageService.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            model=model,
            provider=provider,
            tokens_used=None,  # TODO: Extract from LLM response if available
            user_id=1,  # Assistant UserId
            thinking=thinking_content if thinking_content else None
        )

        # =================================================================
        # Step 5a: Link any artifacts created during this response
        # =================================================================
        MessageService.link_artifacts(conversation_id, assistant_message.id)

        # =================================================================
        # Step 5b: Update and save conversation state
        # =================================================================
        state_handler.append_to_summary(user_message=message, assistant_reply=response)
        state_handler.increment_turn()
        ConversationStateService.save_state(conversation_id, state_handler.to_dict())

        # =================================================================
        # Step 6: Update conversation summary
        # =================================================================
        if provider == "anthropic":
            client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY")).client
        else:
            client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY")).client

        generated_title = None
        if is_new_conversation:
            generated_title = ConversationSummaryHelper.generate_title(message, client=client, provider=provider)
            conversation = ConversationService.update_conversation(conversation_id, user.id, {"title": generated_title})

        messages = MessageService.get_messages(conversation_id)
        message_count = len(messages)

        preview = ConversationSummaryHelper.get_last_message_preview(messages, max_length=100)
        ConversationService.update_conversation(conversation_id, user.id, {"last_message_preview": preview})

        if ConversationSummaryHelper.should_update_summary(message_count):
            new_summary = ConversationSummaryHelper.build_summary(messages, client=client, provider=provider)
            ConversationService.update_conversation(conversation_id, user.id, {"summary": new_summary})

        # =================================================================
        # Step 7: Return response with conversation_id
        # =================================================================
        result = {
            "response": response,
            "conversation_id": conversation_id
        }
        if generated_title:
            result["title"] = generated_title

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/stream")
async def chat_stream(
        message: str,
        model: str = None,
        provider: str = None,
        conversation_id: int = None,
        project_id: int = None,
        user: User = Depends(require_active_user),
        openai_message_handler=Depends(get_openai_message_handler),
        anthropic_message_handler=Depends(get_anthropic_message_handler)
):
    """
    Stream a chat response via Server-Sent Events (SSE).

    Args:
        message: The user's message
        model: Model to use (optional - falls back to user's default)
        provider: Provider to use (optional - falls back to user's default)
        conversation_id: Conversation to continue (optional)
        project_id: Project context (optional - applies custom instructions, links new convos)
        user: Current authenticated user

    Returns:
        StreamingResponse with SSE events
    """

    # Resolve provider and model from user settings
    settings = UserSettingsService.get_settings(user.id)

    if model and not provider:
        provider = get_provider(model)
        if not provider:
            provider = settings.provider
    elif provider and not model:
        model = settings.default_model
    elif not provider and not model:
        provider = settings.provider
        model = settings.default_model

    # Get model capabilities and user preferences
    capabilities = get_capabilities(model)
    enable_thinking = (
            capabilities.reasoning_type == "extended_thinking"
            and settings.enable_extended_thinking
    )
    thinking_budget = settings.anthropic_thinking_budget

    # Get project instructions if project context provided
    project_instructions = get_project_instructions(project_id, user.id)

    # Get or create conversation
    is_new_conversation = False
    if conversation_id:
        conversation = ConversationService.get_conversation(conversation_id, user.id)
        if conversation is None:
            async def error_gen():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Conversation not found'})}\n\n"

            return StreamingResponse(error_gen(), media_type="text/event-stream")
    else:
        is_new_conversation = True
        conversation = ConversationService.create_conversation(user.id, title="New Conversation")
        conversation_id = conversation.id
        
        # Link to project if project_id provided
        if project_id:
            link_conversation_to_project(conversation_id, project_id, user.id)

    # Load or create conversation state
    saved_state = ConversationStateService.get_state(conversation_id)
    if saved_state:
        state_handler = StateHandler.from_dict(conversation_id, saved_state)
    else:
        state_handler = StateHandler(conversation_id)

    state_handler.update_state_from_message(message)

    # Save user message
    MessageService.add_message(
        conversation_id=conversation_id,
        role="user",
        content=message,
        model=model,
        provider=provider,
        tokens_used=None,
        user_id=user.id
    )

    # Build instructions with memories and project instructions
    state = state_handler.get_state()
    state["conversation_id"] = conversation_id  # Add for recent exchanges lookup
    memories = MemoryService.get_memories(user.id, limit=settings.memory_limit)
    memories_text = MemoryService.format_for_prompt(memories)
    instructions = Instructions(
        state, 
        user=user, 
        memories_text=memories_text,
        project_instructions=project_instructions
    ).build_instructions()
    tool_context = {"user_id": user.id, "user_role": user.role, "conversation_id": conversation_id}

    async def event_generator():
        full_response = ""
        full_thinking = ""
        
        # Track content blocks for persistence
        content_blocks = []
        current_thinking_content = ""
        current_text_content = ""

        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"

            if provider == "anthropic":
                async for event in anthropic_message_handler.handle_message_stream(
                        instructions=instructions,
                        message=message,
                        model=model,
                        enable_thinking=enable_thinking,
                        thinking_budget=thinking_budget,
                        tool_context=tool_context
                ):
                    event_type = event.get("type")
                    
                    # Track content blocks based on event type
                    if event_type == "thinking_start":
                        current_thinking_content = ""
                    elif event_type == "thinking":
                        text = event.get("text", "")
                        full_thinking += text
                        current_thinking_content += text
                    elif event_type == "thinking_end":
                        # Finalize thinking block
                        content_blocks.append({
                            "type": "thinking",
                            "content": current_thinking_content
                        })
                        current_thinking_content = ""
                    elif event_type == "content_start":
                        current_text_content = ""
                    elif event_type == "content":
                        text = event.get("text", "")
                        full_response += text
                        current_text_content += text
                    elif event_type == "content_end":
                        # Finalize text block
                        if current_text_content:
                            content_blocks.append({
                                "type": "text",
                                "content": current_text_content
                            })
                        current_text_content = ""
                    elif event_type == "tool_start":
                        # Add tool call block (params will be added on tool_end)
                        content_blocks.append({
                            "type": "tool_call",
                            "name": event.get("name"),
                            "params": {},
                            "isComplete": False
                        })
                    elif event_type == "tool_end":
                        # Update the matching tool block with params and result
                        tool_name = event.get("name")
                        for block in reversed(content_blocks):
                            if block.get("type") == "tool_call" and block.get("name") == tool_name and not block.get("isComplete"):
                                block["params"] = event.get("params", {})
                                block["result"] = event.get("result")
                                block["isComplete"] = True
                                break
                    elif event_type == "done":
                        full_response = event.get("full_response", full_response)
                        # Handle any remaining text content not closed by content_end
                        if current_text_content:
                            content_blocks.append({
                                "type": "text",
                                "content": current_text_content
                            })
                    
                    yield f"data: {json.dumps(event)}\n\n"
            else:
                async for event in openai_message_handler.handle_message_stream(
                        instructions=instructions,
                        message=message,
                        model=model,
                        tool_context=tool_context
                ):
                    event_type = event.get("type")
                    
                    if event_type == "content":
                        text = event.get("text", "")
                        full_response += text
                        current_text_content += text
                    elif event_type == "tool_start":
                        content_blocks.append({
                            "type": "tool_call",
                            "name": event.get("name"),
                            "params": {},
                            "isComplete": False
                        })
                    elif event_type == "tool_end":
                        tool_name = event.get("name")
                        for block in reversed(content_blocks):
                            if block.get("type") == "tool_call" and block.get("name") == tool_name and not block.get("isComplete"):
                                block["params"] = event.get("params", {})
                                block["result"] = event.get("result")
                                block["isComplete"] = True
                                break
                    elif event_type == "done":
                        full_response = event.get("full_response", full_response)
                        # Add final text block if there's content
                        if current_text_content:
                            content_blocks.append({
                                "type": "text",
                                "content": current_text_content
                            })
                    
                    yield f"data: {json.dumps(event)}\n\n"

            # Serialize content blocks to JSON for storage
            content_blocks_json = json.dumps(content_blocks) if content_blocks else None

            # Save assistant message (with thinking and content_blocks)
            assistant_message = MessageService.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                model=model,
                provider=provider,
                tokens_used=None,
                user_id=1,
                thinking=full_thinking if full_thinking else None,
                content_blocks=content_blocks_json
            )

            # Link any artifacts created during this response
            MessageService.link_artifacts(conversation_id, assistant_message.id)

            # Create client for summary operations
            if provider == "anthropic":
                client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY")).client
            else:
                client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY")).client

            # Update title if new conversation
            generated_title = None
            if is_new_conversation:
                generated_title = ConversationSummaryHelper.generate_title(message, client=client, provider=provider)
                ConversationService.update_conversation(conversation_id, user.id, {"title": generated_title})

            # Update preview and summary
            messages = MessageService.get_messages(conversation_id)
            message_count = len(messages)
            
            preview = ConversationSummaryHelper.get_last_message_preview(messages, max_length=100)
            ConversationService.update_conversation(conversation_id, user.id, {"last_message_preview": preview})

            if ConversationSummaryHelper.should_update_summary(message_count):
                new_summary = ConversationSummaryHelper.build_summary(messages, client=client, provider=provider)
                ConversationService.update_conversation(conversation_id, user.id, {"summary": new_summary})

            # Update and save conversation state
            state_handler.append_to_summary(user_message=message, assistant_reply=full_response)
            state_handler.increment_turn()
            ConversationStateService.save_state(conversation_id, state_handler.to_dict())

            # Final event
            final_event = {"type": "stream_end", "conversation_id": conversation_id}
            if generated_title:
                final_event["title"] = generated_title
            yield f"data: {json.dumps(final_event)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
