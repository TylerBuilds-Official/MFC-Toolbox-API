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
from src.data.model_capabilities import get_capabilities, get_provider
from src.data.instructions import Instructions
from src.tools.state.state_handler import StateHandler
from src.api.dependencies import get_openai_message_handler, get_anthropic_message_handler


router = APIRouter()

@router.get("/chat")
async def chat(message: str, model: str = None,
               provider: str = None, conversation_id: int = None,
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
        instructions_text = Instructions(state, user=user, memories_text=memories_text).build_instructions()
        tool_context = {"user_id": user.id, "user_role": user.role, "conversation_id": conversation_id}

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

    # Build instructions with memories
    state = state_handler.get_state()
    memories = MemoryService.get_memories(user.id, limit=settings.memory_limit)
    memories_text = MemoryService.format_for_prompt(memories)
    instructions = Instructions(state, user=user, memories_text=memories_text).build_instructions()
    tool_context = {"user_id": user.id, "user_role": user.role, "conversation_id": conversation_id}

    async def event_generator():
        full_response = ""
        full_thinking = ""

        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"

            if provider == "anthropic":
                for event in anthropic_message_handler.handle_message_stream(
                        instructions=instructions,
                        message=message,
                        model=model,
                        enable_thinking=enable_thinking,
                        thinking_budget=thinking_budget,
                        tool_context=tool_context
                ):
                    if event.get("type") == "content":
                        full_response += event.get("text", "")
                    elif event.get("type") == "thinking":
                        full_thinking += event.get("text", "")
                    elif event.get("type") == "done":
                        full_response = event.get("full_response", full_response)
                    yield f"data: {json.dumps(event)}\n\n"
            else:
                for event in openai_message_handler.handle_message_stream(
                        instructions=instructions,
                        message=message,
                        model=model,
                        tool_context=tool_context
                ):
                    if event.get("type") == "content":
                        full_response += event.get("text", "")
                    elif event.get("type") == "done":
                        full_response = event.get("full_response", full_response)
                    yield f"data: {json.dumps(event)}\n\n"

            # Save assistant message (with thinking if present)
            assistant_message = MessageService.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                model=model,
                provider=provider,
                tokens_used=None,
                user_id=1,
                thinking=full_thinking if full_thinking else None
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
