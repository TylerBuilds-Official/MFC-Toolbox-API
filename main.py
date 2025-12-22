from dotenv import load_dotenv

from src.utils._dataclasses_main.create_conversation_request import CreateConversationRequest

load_dotenv()

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import src.utils._dataclasses_main

from src.tools.org_tools.get_models import get_models
from src.tools.sql_tools import close_mysql_pool, close_mssql_pool
from src.tools.routers.chat_router import ChatRouter
from src.tools.state.state_handler import StateHandler
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS as tool_definitions

from src.tools.openai_chat.client import OpenAIClient
from src.tools.openai_chat.handlers.openai_conversation_handler import OpenAIConversationHandler
from src.tools.openai_chat.handlers.openai_message_handler import OpenAIMessageHandler

from src.tools.anthropic_chat.client import AnthropicClient
from src.tools.anthropic_chat.handlers.anthropic_conversation_handler import AnthropicConversationHandler
from src.tools.anthropic_chat.handlers.anthropic_message_handler import AnthropicMessageHandler

from src.tools.auth.azure_auth import azure_scheme
from src.tools.auth import User, get_current_user, require_role, require_active_user
from src.tools.auth.user_service import UserService

from src.utils.settings_utils import UserSettingsService
from src.utils.conversation_utils import ConversationService, MessageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all providers and router"""
    try:
        print("[STARTUP] Initializing application...")
        print(f"[STARTUP] Azure Client ID: {os.getenv('AZURE_CLIENT_ID')}")
        print(f"[STARTUP] Azure Tenant ID: {os.getenv('AZURE_TENANT_ID')}")

        # State handler still in-memory (per-user conversations coming in Phase 2)
        app.state.state_handler = StateHandler()

        openai_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY")).client
        openai_message_handler = OpenAIMessageHandler(client=openai_client)
        openai_conversation_handler = OpenAIConversationHandler(
            state_handler=app.state.state_handler,
            message_handler=openai_message_handler
        )

        anthropic_client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY")).client
        anthropic_message_handler = AnthropicMessageHandler(client=anthropic_client)
        anthropic_conversation_handler = AnthropicConversationHandler(
            state_handler=app.state.state_handler,
            message_handler=anthropic_message_handler
        )

        # ChatRouter no longer needs settings_manager - provider/model passed explicitly
        app.state.chat_router = ChatRouter(
            settings_manager=None,
            state_handler=app.state.state_handler,
            openai_handler=openai_conversation_handler,
            anthropic_handler=anthropic_conversation_handler
        )

    except Exception as e:
        print(f"Error initializing: {e}")
        raise

    yield

    # Cleanup both pools on shutdown
    close_mysql_pool()
    close_mssql_pool()


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
            provider = ChatRouter.infer_provider_from_model(model)
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
        if conversation_id:
            # Verify ownership
            conversation = ConversationService.get_conversation(conversation_id, user.id)
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Auto-create new conversation
            conversation = ConversationService.create_conversation(
                user.id,
                title="New Conversation"
            )
            conversation_id = conversation.id

        # =================================================================
        # Step 3: Save user message to database
        # =================================================================
        MessageService.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            model=model,
            provider=provider,
            tokens_used=None  # We don't track input tokens currently
        )

        # =================================================================
        # Step 4: Get response from LLM
        # =================================================================
        response = app.state.chat_router.handle_message(
            user_message=message,
            model=model,
            provider=provider
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
            tokens_used=None  # TODO: Extract from LLM response if available
        )

        # =================================================================
        # Step 6: Update conversation summary
        # =================================================================
        # Truncate messages for summary
        user_summary = message[:120] + "..." if len(message) > 120 else message
        assistant_summary = response[:120] + "..." if len(response) > 120 else response

        # Append to existing summary
        current_summary = conversation.summary or ""
        new_summary = (
            f"{current_summary}"
            f"User: {user_summary}\n"
            f"Assistant: {assistant_summary}\n"
        )

        # Optionally limit total summary length (e.g., last 2000 chars)
        if len(new_summary) > 2000:
            new_summary = new_summary[-2000:]

        ConversationService.update_conversation_summary(conversation_id, new_summary)

        # =================================================================
        # Step 7: Return response with conversation_id
        # =================================================================
        return {
            "response": response,
            "conversation_id": conversation_id
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
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
async def get_provider(user: User = Depends(get_current_user)):
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
    """Get available tools."""
    return {"open_ai_tools": tool_definitions}


@app.post("/reset")
async def reset_conversation(user: User = Depends(get_current_user)):
    """Reset the conversation state for a fresh start."""
    app.state.state_handler.reset()
    return {"status": "Conversation reset"}



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