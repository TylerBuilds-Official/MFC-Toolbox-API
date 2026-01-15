import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.tools.openai_chat.client import OpenAIClient
from src.tools.anthropic_chat.client import AnthropicClient

from src.tools.anthropic_chat.handlers.anthropic_message_handler import AnthropicMessageHandler
from src.tools.openai_chat.handlers.openai_message_handler import OpenAIMessageHandler

from src.tools.sql_tools import close_mysql_pool, close_mssql_pool, close_voltron_pool

from src.utils.agent_utils import agent_registry


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
        
        # Store agent registry reference (singleton, but available via app.state too)
        app.state.agent_registry = agent_registry
        print("[STARTUP] Agent registry initialized - WebSocket endpoint: /agent/ws")

    except Exception as e:
        print(f"Error initializing: {e}")
        raise

    yield

    # Cleanup all pools on shutdown
    close_mysql_pool()
    close_mssql_pool()
    close_voltron_pool()
    
    print("[SHUTDOWN] Application shutdown complete")
