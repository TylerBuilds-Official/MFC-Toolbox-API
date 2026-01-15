from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.agent_utils import agent_registry

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
        
        # Register the agent
        hostname = registration.get("hostname", "unknown")
        username = registration.get("username", "unknown")
        version = registration.get("version", "unknown")
        capabilities = registration.get("capabilities", [])
        
        agent = await agent_registry.register(
            websocket=websocket,
            hostname=hostname,
            username=username,
            version=version,
            capabilities=capabilities
        )
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "registered",
            "agent_id": agent.agent_id,
            "message": "Successfully registered with central API"
        })
        
        # Listen for responses
        while True:
            message = await websocket.receive_json()
            
            # Route response to waiting command
            handled = agent_registry.handle_response(username, message)
            
            if not handled:
                print(f"[AGENT_WS] Unhandled message from {username}: {message}")
    
    except WebSocketDisconnect:
        print(f"[AGENT_WS] Agent disconnected: {username or 'unknown'}")
    
    except Exception as e:
        print(f"[AGENT_WS] Error: {e}")
    
    finally:
        if username:
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
    
    return {"connected": False}
