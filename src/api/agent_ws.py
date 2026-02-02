from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.agent_utils import agent_registry
from src.utils.connector_utils import (
    upsert_registered_agent,
    update_agent_last_seen,
    get_registered_agent_by_username
)

router = APIRouter(prefix="/agent")


@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for ToolboxAgentExecutor connections.
    
    Protocol:
    1. Agent connects
    2. Agent sends registration message: {"type": "register", "hostname": "...", "username": "...", ...}
    3. Server acknowledges: {"type": "registered", "agent_id": "..."}
    4. Server sends commands: {"command_id": "...", "module": "...", "action": "...", "params": {...}}
    5. Agent sends responses: {"command_id": "...", "success": true/false, ...}
    """
    await websocket.accept()
    
    agent = None
    username = None
    
    try:
        # Wait for registration message
        registration = await websocket.receive_json()
        
        if registration.get("type") != "register":
            await websocket.close(code=1002, reason="Expected registration message")
            return
        
        # Extract registration info
        hostname = registration.get("hostname", "unknown")
        username = registration.get("username", "unknown")
        version = registration.get("version", "unknown")
        capabilities = registration.get("capabilities", [])
        
        # Register in-memory (for active connections)
        agent = await agent_registry.register(
            websocket=websocket,
            hostname=hostname,
            username=username,
            version=version,
            capabilities=capabilities
        )
        
        # Persist to database
        # Note: We use username as a placeholder for user_id until we can map it
        # The actual Azure AD user_id will be linked when user accesses settings
        try:
            upsert_registered_agent(
                user_id=username.lower(),  # Temporary - will be replaced with Azure AD ID
                username=username,
                hostname=hostname,
                agent_version=version
            )
            print(f"[AGENT_WS] Persisted agent registration to DB: {username}")
        except Exception as db_error:
            # Don't fail connection if DB persistence fails
            print(f"[AGENT_WS] Warning: Could not persist agent to DB: {db_error}")
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "registered",
            "agent_id": agent.agent_id,
            "message": "Successfully registered with central API"
        })
        
        # Listen for responses
        while True:
            try:
                message = await websocket.receive_json()
            except ValueError as e:
                # Malformed JSON from agent - log but keep connection alive
                print(f"[AGENT_WS] Invalid JSON from {username}: {e}")
                continue
            
            try:
                # Route response to waiting command
                handled = agent_registry.handle_response(username, message)
                
                if not handled:
                    # Pong, ack, or other non-command response
                    msg_type = message.get("type", "unknown")
                    if msg_type not in ("pong", "update_ack"):
                        print(f"[AGENT_WS] Unhandled message from {username}: {msg_type}")
            except Exception as e:
                print(f"[AGENT_WS] Error handling message from {username}: {e}")
    
    except WebSocketDisconnect:
        print(f"[AGENT_WS] Agent disconnected: {username or 'unknown'}")
    
    except Exception as e:
        print(f"[AGENT_WS] Connection error: {e}")
    
    finally:
        # Fail any pending commands so they don't hang until timeout
        if username:
            agent = agent_registry.get_agent(username)
            if agent:
                for cmd_id, future in list(agent.pending_commands.items()):
                    if not future.done():
                        future.set_result({
                            "command_id": cmd_id,
                            "success": False,
                            "error": "Agent disconnected while processing command"
                        })
            await agent_registry.unregister(username)


@router.get("/connected")
async def list_connected_agents():
    """List all connected agents (admin/debug endpoint)."""
    return {
        "agents": agent_registry.list_agents(),
        "count": len(agent_registry.list_agents())
    }


@router.get("/status/{username}")
async def check_agent_status(username: str):
    """Check if a specific user has a connected agent."""
    agent = agent_registry.get_agent(username)
    
    if agent:
        return {
            "connected": True,
            "hostname": agent.hostname,
            "version": agent.version,
            "capabilities": agent.capabilities,
            "connected_at": agent.connected_at.isoformat()
        }
    
    # Check DB for historical registration even if not currently connected
    db_agent = get_registered_agent_by_username(username)
    if db_agent:
        return {
            "connected": False,
            "hostname": db_agent.hostname,
            "version": db_agent.agent_version,
            "last_seen": db_agent.last_seen_at.isoformat() if db_agent.last_seen_at else None,
            "first_registered": db_agent.first_registered_at.isoformat() if db_agent.first_registered_at else None
        }
    
    return {"connected": False}
