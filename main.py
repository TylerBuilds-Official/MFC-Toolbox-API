from dotenv import load_dotenv
load_dotenv()

import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from src.utils._dataclasses_main.update_conversation_request import UpdateConversationRequest
from src.utils._dataclasses_main.create_conversation_request import CreateConversationRequest

from src.tools.org_tools.get_models import get_models
from src.tools.sql_tools import close_mysql_pool, close_mssql_pool
from src.tools.sql_tools.voltron_pool import close_voltron_pool
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS as tool_definitions
from src.tools.tool_registry import get_chat_tools, get_data_tools

from src.tools.openai_chat.client import OpenAIClient
from src.tools.openai_chat.handlers.openai_message_handler import OpenAIMessageHandler

from src.tools.anthropic_chat.client import AnthropicClient
from src.tools.anthropic_chat.handlers.anthropic_message_handler import AnthropicMessageHandler

from src.tools.auth.azure_auth import azure_scheme
from src.tools.auth import User, get_current_user, require_role, require_active_user
from src.tools.auth.user_service import UserService

from src.utils.settings_utils import UserSettingsService
from src.utils.conversation_utils import ConversationService, MessageService
from src.utils.conversation_utils.summary_helper import SummaryHelper
from src.utils.memory_utils import MemoryService
from src.utils.conversation_state_utils import ConversationStateService
from src.data.model_capabilities import get_capabilities, get_provider
from src.data.instructions import Instructions
from src.tools.state.state_handler import StateHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all providers and router"""
    try:
        print("[STARTUP] Initializing application...")
        print(f"[STARTUP] Azure Client ID: {os.getenv('AZURE_CLIENT_ID')}")
        print(f"[STARTUP] Azure Tenant ID: {os.getenv('AZURE_TENANT_ID')}")

        openai_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY")).client
        openai_message_handler = OpenAIMessageHandler(client=openai_client)

        anthropic_client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY")).client
        anthropic_message_handler = AnthropicMessageHandler(client=anthropic_client)

        # Store message handlers directly for endpoint access
        app.state.openai_message_handler = openai_message_handler
        app.state.anthropic_message_handler = anthropic_message_handler

    except Exception as e:
        print(f"Error initializing: {e}")
        raise

    yield

    # Cleanup all pools on shutdown
    close_mysql_pool()
    close_mssql_pool()
    close_voltron_pool()


app = FastAPI(
    title="MFC Toolbox API",
    description="Multi-user chat interface for Metals Fabrication Company",
    version="0.3.0",
    lifespan=lifespan,
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": os.getenv("AZURE_CLIENT_ID"),
    },
)

# CORS middleware - allows WebUI to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:5173",
        "https://10.0.59.72:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to log all requests and responses
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"\n[REQUEST] {request.method} {request.url.path}")
    print(f"[REQUEST] Headers: {dict(request.headers)}")

    try:
        response = await call_next(request)
        print(f"[RESPONSE] Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"[ERROR] Exception during request: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


# Exception handler for auth errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"[ERROR] Unhandled exception: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()

    # Return generic error
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# =============================================================================
# Public endpoints (no auth required)
# =============================================================================

@app.get("/")
async def root():
    return {"health": "Healthy", "status": "Running.."}


@app.get("/auth/debug")
async def debug_auth():
    """Debug endpoint to check Azure AD configuration"""
    return {
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "openid_config_loaded": azure_scheme.openid_config.authorization_endpoint is not None,
        "authorization_endpoint": azure_scheme.openid_config.authorization_endpoint,
    }


@app.get("/models")
async def get_all_models():
    data = get_models()
    return {"models": data}


# =============================================================================
# Protected endpoints (require authenticated user)
# =============================================================================

@app.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    print(f"[/me] Returning user info for: {user.email}")
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
    }


@app.get("/chat")
async def chat(message: str, model: str = None,
               provider: str = None, conversation_id: int = None,
               user: User = Depends(require_active_user)):
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
        tool_context = {"user_id": user.id, "conversation_id": conversation_id}
        
        if provider == "anthropic":
            response = app.state.anthropic_message_handler.handle_message(
                instructions=instructions_text,
                message=message,
                model=model,
                tool_context=tool_context
            )
        else:
            response = app.state.openai_message_handler.handle_message(
                instructions=instructions_text,
                message=message,
                model=model,
                tool_context=tool_context
            )

        # =================================================================
        # Step 5: Save assistant message to database
        # =================================================================
        MessageService.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            model=model,
            provider=provider,
            tokens_used=None,  # TODO: Extract from LLM response if available
            user_id=1 # Assistant UserId
        )

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
            generated_title = SummaryHelper.generate_title(message, client=client, provider=provider)
            conversation = ConversationService.update_conversation(conversation_id, user.id, {"title": generated_title})

        messages = MessageService.get_messages(conversation_id)
        message_count = len(messages)

        preview = SummaryHelper.get_last_message_preview(messages, max_length=100)
        ConversationService.update_conversation(conversation_id, user.id, {"last_message_preview": preview})

        if SummaryHelper.should_update_summary(message_count):
            new_summary = SummaryHelper.build_summary(messages, client=client, provider=provider)
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


# =============================================================================
# Data Visualization endpoints
# =============================================================================

from src.utils.data_utils import (
    DataSessionService, 
    DataResultService, 
    DataExecutionService
)
from src.utils._dataclasses_main.create_data_session_request import CreateDataSessionRequest
from src.utils._dataclasses_main.update_data_session_request import UpdateDataSessionRequest

# Initialize execution service
_data_execution_service = DataExecutionService()


@app.get("/data/tools")
async def get_data_tools_endpoint(user: User = Depends(require_active_user)):
    """Get list of tools available for data visualization, filtered by user role."""
    return {"tools": _data_execution_service.get_available_tools(user.role)}


@app.post("/data/sessions")
async def create_data_session(
    body: CreateDataSessionRequest,
    user: User = Depends(require_active_user)
):
    """
    Create a new data session (draft, not executed).
    
    Returns session with status='pending'.
    Call POST /data/sessions/{id}/execute to run the tool.
    """
    session = DataSessionService.create_session(
        user_id=user.id,
        tool_name=body.tool_name,
        tool_params=body.tool_params,
        message_id=body.message_id,
        parent_session_id=body.parent_session_id,
        visualization_config=body.visualization_config
    )
    return session.to_dict()


@app.get("/data/sessions")
async def list_data_sessions(
    limit: int = 50,
    offset: int = 0,
    tool_name: str = None,
    status: str = None,
    user: User = Depends(require_active_user)
):
    """List data sessions for current user with optional filtering."""
    sessions = DataSessionService.list_sessions(
        user_id=user.id,
        limit=limit,
        offset=offset,
        tool_name=tool_name,
        status=status
    )
    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }


@app.get("/data/sessions/{session_id}")
async def get_data_session(
    session_id: int,
    user: User = Depends(require_active_user)
):
    """Get a specific data session with has_results flag."""
    result = DataSessionService.get_session_with_has_results(session_id, user.id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result


@app.patch("/data/sessions/{session_id}")
async def update_data_session(
    session_id: int,
    body: UpdateDataSessionRequest,
    user: User = Depends(require_active_user)
):
    """Update session visualization config or other fields."""
    updates = {}
    
    if body.visualization_config is not None:
        updates["visualization_config"] = body.visualization_config
    if body.status is not None:
        updates["status"] = body.status
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    session = DataSessionService.update_session(session_id, user.id, updates)
    
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()


@app.post("/data/sessions/{session_id}/execute")
async def execute_data_session(
    session_id: int,
    user: User = Depends(require_active_user)
):
    """
    Execute the tool for a session and store results.
    
    Flow:
    1. Verify user has permission for the tool
    2. Sets status to 'running'
    3. Executes the MCP tool
    4. Normalizes and stores results
    5. Sets status to 'success' or 'error'
    
    Returns the updated session and result (if successful).
    """
    # Verify ownership
    session = DataSessionService.get_session(session_id, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        updated_session, result = _data_execution_service.execute(session_id, user.role)
        
        response = {
            "session": updated_session.to_dict(),
            "success": updated_session.status == "success"
        }
        
        if result:
            response["result"] = result.to_dict()
        
        return response
    
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.get("/data/sessions/{session_id}/results")
async def get_data_session_results(
    session_id: int,
    user: User = Depends(require_active_user)
):
    """Get the result payload for a session."""
    # Verify ownership
    session = DataSessionService.get_session(session_id, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = DataResultService.get_result(session_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="No results found for session")
    
    return result.to_dict()


@app.get("/data/sessions/groups/{group_id}")
async def get_data_session_group(
    group_id: int,
    user: User = Depends(require_active_user)
):
    """Get all sessions in a lineage group."""
    sessions = DataSessionService.get_session_lineage(group_id, user.id)
    
    if not sessions:
        raise HTTPException(status_code=404, detail="Session group not found")
    
    return {
        "group_id": group_id,
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }


@app.get("/chat/stream")
async def chat_stream(
    message: str,
    model: str = None,
    provider: str = None,
    conversation_id: int = None,
    user: User = Depends(require_active_user)
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
    tool_context = {"user_id": user.id, "conversation_id": conversation_id}


    async def event_generator():
        full_response = ""
        full_thinking = ""
        
        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"
            
            if provider == "anthropic":
                handler = app.state.anthropic_message_handler
                for event in handler.handle_message_stream(
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
                handler = app.state.openai_message_handler
                for event in handler.handle_message_stream(
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
            MessageService.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                model=model,
                provider=provider,
                tokens_used=None,
                user_id=1,
                thinking=full_thinking if full_thinking else None
            )
            
            # Update title if new conversation
            generated_title = None
            if is_new_conversation:
                client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY")).client if provider == "anthropic" else OpenAIClient(api_key=os.getenv("OPENAI_API_KEY")).client
                generated_title = SummaryHelper.generate_title(message, client=client, provider=provider)
                ConversationService.update_conversation(conversation_id, user.id, {"title": generated_title})
            
            # Update preview
            messages = MessageService.get_messages(conversation_id)
            preview = SummaryHelper.get_last_message_preview(messages, max_length=100)
            ConversationService.update_conversation(conversation_id, user.id, {"last_message_preview": preview})
            
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


@app.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    """Get current user's settings."""
    settings = UserSettingsService.get_settings(user.id)
    return settings.to_dict()


@app.post("/settings")
async def update_settings(updates: dict, user: User = Depends(get_current_user)):
    """Bulk update user settings."""
    try:
        settings = UserSettingsService.update_settings(user.id, updates)
        return {"status": "settings updated", "settings": settings.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/settings/provider")
async def get_provider_settings(user: User = Depends(get_current_user)):
    """Get user's current provider and default model."""
    settings = UserSettingsService.get_settings(user.id)
    return {
        "provider": settings.provider,
        "default_model": settings.default_model
    }


@app.post("/settings/provider")
async def set_provider(
        provider: str,
        default_model: str = None,
        user: User = Depends(get_current_user)
):
    """Set user's provider preference (and optionally default model)."""
    try:
        settings = UserSettingsService.update_provider(user.id, provider, default_model)
        return {
            "status": "updated",
            "provider": settings.provider,
            "default_model": settings.default_model
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tools")
async def get_tools(user: User = Depends(get_current_user)):
    """Get available chat tools, filtered by user role."""
    return {"open_ai_tools": get_chat_tools(user.role)}


@app.post("/reset")
async def reset_conversation(conversation_id: int = None, user: User = Depends(get_current_user)):
    """
    Reset the conversation state for a specific conversation.
    If no conversation_id provided, returns an error.
    """
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")
    
    # Verify ownership
    conversation = ConversationService.get_conversation(conversation_id, user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save fresh state
    fresh_state = StateHandler(conversation_id)
    ConversationStateService.save_state(conversation_id, fresh_state.to_dict())
    
    return {"status": "Conversation state reset", "conversation_id": conversation_id}



# =============================================================================
# Conversation management endpoints
# =============================================================================


@app.get("/conversations")
async def list_conversations(include_inactive=False, user: User = Depends(require_active_user)):
    conversations = ConversationService.list_conversations(user.id, include_inactive=include_inactive)
    #TODO add admin guard against including inactive conversations
    return {
        "conversations": [conversation.to_dict() for conversation in conversations]
    }

@app.post("/conversations")
async def create_conversation(body: CreateConversationRequest, user: User = Depends(require_active_user)):
    title = body.title if body else "New Conversation"
    conversation = ConversationService.create_conversation(user.id, title=title)
    return conversation.to_dict()


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, user: User = Depends(require_active_user)):
    conversation = ConversationService.get_conversation(conversation_id, user.id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = MessageService.get_messages(conversation_id)

    return {
        "conversation": conversation.to_dict(),
        "messages": [msg.to_dict() for msg in messages]
    }


@app.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: int,
        body: UpdateConversationRequest,
        user: User = Depends(require_active_user)
):
    updates = {}
    if body.title is not None:
        updates["title"] = body.title

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    conversation = ConversationService.update_conversation(
        conversation_id,
        user.id,
        updates
    )

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation.to_dict()


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, user: User = Depends(require_active_user)):
    deleted = ConversationService.delete_conversation(conversation_id, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "status": "deleted",
        "conversation_id": conversation_id
    }


# =============================================================================
# Admin endpoints (require admin role)
# =============================================================================

@app.get("/admin/users")
async def list_all_users(user: User = Depends(require_role("admin"))):
    """List all users in the system."""
    users = UserService.list_users()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in users
        ]
    }


@app.post("/admin/users/{user_id}/role")
async def set_user_role(
        user_id: int,
        role: str,
        user: User = Depends(require_role("admin"))
):
    """Set a user's role (admin only)."""
    try:
        success = UserService.set_user_role(user_id, role)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "updated", "user_id": user_id, "role": role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))