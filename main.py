import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.tools.org_tools.get_models import get_models
from src.tools.sql_tools.pool import close_pool
from src.tools.routers.chat_router import ChatRouter
from src.tools.state.state_handler import StateHandler
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS as oa_tool_definitions
from src.tools.state.settings_manager import SettingsManager

from src.tools.openai_chat.client import OpenAIClient
from src.tools.openai_chat.handlers.openai_conversation_handler import OpenAIConversationHandler
from src.tools.openai_chat.handlers.openai_message_handler import OpenAIMessageHandler

from src.tools.anthropic_chat.client import AnthropicClient
from src.tools.anthropic_chat.handlers.anthropic_conversation_handler import AnthropicConversationHandler
from src.tools.anthropic_chat.handlers.anthropic_message_handler import AnthropicMessageHandler





load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all providers and router"""
    try:
        app.state.settings_manager = SettingsManager()
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

        app.state.chat_router = ChatRouter(
                                settings_manager=app.state.settings_manager,
                                state_handler=app.state.state_handler,
                                openai_handler=openai_conversation_handler,
                                anthropic_handler=anthropic_conversation_handler
        )

    except Exception as e:
        print(f"Error initializing: {e}")
        raise

    yield
    close_pool()


app = FastAPI(
    title="MFC Toolbox API",
    description="MVP single-user, single-session chat interface for Metals Fabrication Company",
    version="0.1.0",
    lifespan=lifespan
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


@app.get("/")
async def root():
    return {"health": "Healthy", "status": "Running.."}


@app.get("/chat")
async def chat(message: str, model: str = None, provider: str = None):
    try:
        response = app.state.chat_router.handle_message(
            user_message=message, model=model, provider=provider)
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/settings")
async def get_settings():
    return app.state.settings_manager.get_all_settings()

@app.post("/settings")
async def update_settings(updates: dict):
    app.state.settings_manager.update_settings(updates)
    return {"status": "settings updated", "updates": updates}

@app.get("/settings/provider")
async def get_provider():
    return {"provider": app.state.settings_manager.get_provider(),
            "default_model": app.state.settings_manager.get_default_model()}

@app.post("/settings/provider")
async def set_provider(provider: str, default_model: str = None):
    """Set provider preference"""
    try:
        app.state.settings_manager.set_provider(provider)
        if default_model:
            app.state.settings_manager.set_default_model(default_model)
        return {
            "status": "updated",
            "provider": provider,
            "default_model": default_model or app.state.settings_manager.get_default_model()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tools")
async def get_tools():
    return {"open_ai_tools": oa_tool_definitions}

@app.get("/models")
async def get_all_models():
    data = get_models()
    return {"models": data}

@app.post("/reset")
async def reset_conversation():
    """Reset the conversation state for a fresh start."""
    app.state.state_handler.reset()
    return {"status": "Conversation reset"}


