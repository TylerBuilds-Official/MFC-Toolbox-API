import asyncio
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from fastapi import WebSocket


@dataclass
class ConnectedAgent:
    """Represents a connected agent."""
    agent_id: str
    websocket: WebSocket
    hostname: str
    username: str
    version: str
    capabilities: list[str]
    connected_at: datetime = field(default_factory=datetime.now)
    
    # For tracking pending commands
    pending_commands: dict = field(default_factory=dict)


class AgentRegistry:
    """
    Manages connected ToolboxAgentExecutor instances.
    
    Agents are keyed by username (lowercase) since that maps to the
    authenticated user making requests in the Toolbox.
    """
    
    def __init__(self):
        self._agents: dict[str, ConnectedAgent] = {}
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        websocket: WebSocket,
        hostname: str,
        username: str,
        version: str,
        capabilities: list[str]
    ) -> ConnectedAgent:
        """Register a new agent connection."""
        async with self._lock:
            # Normalize username for consistent lookup
            user_key = username.lower()
            
            # If agent already exists for this user, close old connection
            if user_key in self._agents:
                old_agent = self._agents[user_key]
                print(f"[AGENT_REGISTRY] Replacing existing agent for {user_key}")
                try:
                    await old_agent.websocket.close(code=1000, reason="Replaced by new connection")
                except Exception:
                    pass
            
            agent = ConnectedAgent(
                agent_id=str(uuid.uuid4()),
                websocket=websocket,
                hostname=hostname,
                username=username,
                version=version,
                capabilities=capabilities
            )
            
            self._agents[user_key] = agent
            print(f"[AGENT_REGISTRY] Registered agent: {hostname} ({username}) - capabilities: {capabilities}")
            
            return agent
    
    async def unregister(self, username: str) -> None:
        """Remove an agent from the registry."""
        async with self._lock:
            user_key = username.lower()
            if user_key in self._agents:
                agent = self._agents.pop(user_key)
                print(f"[AGENT_REGISTRY] Unregistered agent: {agent.hostname} ({agent.username})")
    
    def get_agent(self, username: str) -> Optional[ConnectedAgent]:
        """Get agent for a specific user."""
        return self._agents.get(username.lower())
    
    def is_connected(self, username: str) -> bool:
        """Check if user has a connected agent."""
        return username.lower() in self._agents
    
    def list_agents(self) -> list[dict]:
        """List all connected agents (for admin/debug)."""
        return [
            {
                "agent_id": agent.agent_id,
                "hostname": agent.hostname,
                "username": agent.username,
                "version": agent.version,
                "capabilities": agent.capabilities,
                "connected_at": agent.connected_at.isoformat()
            }
            for agent in self._agents.values()
        ]
    
    async def send_command(
        self,
        username: str,
        module: str,
        action: str,
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """
        Send a command to a user's agent and wait for response.
        
        Args:
            username: The user whose agent should execute the command
            module: Target module (e.g., "filesystem")
            action: Action to execute (e.g., "list_directory")
            params: Parameters for the action
            timeout: How long to wait for response
            
        Returns:
            Response dict from agent
            
        Raises:
            ValueError: If no agent connected for user
            TimeoutError: If agent doesn't respond in time
        """
        agent = self.get_agent(username)
        if not agent:
            raise ValueError(f"No agent connected for user: {username}")
        
        if module not in agent.capabilities:
            raise ValueError(f"Agent does not have capability: {module}")
        
        command_id = str(uuid.uuid4())
        command = {
            "command_id": command_id,
            "module": module,
            "action": action,
            "params": params
        }
        
        # Create a future to wait for response
        response_future = asyncio.Future()
        agent.pending_commands[command_id] = response_future
        
        try:
            # Send command
            await agent.websocket.send_json(command)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent did not respond within {timeout}s")
        finally:
            # Cleanup
            agent.pending_commands.pop(command_id, None)
    
    def handle_response(self, username: str, response: dict) -> bool:
        """
        Handle a response from an agent.
        
        Called by the WebSocket handler when agent sends a message.
        Returns True if response was matched to a pending command.
        """
        agent = self.get_agent(username)
        if not agent:
            return False
        
        command_id = response.get("command_id")
        if not command_id:
            return False
        
        future = agent.pending_commands.get(command_id)
        if future and not future.done():
            future.set_result(response)
            return True
        
        return False


# Singleton instance
agent_registry = AgentRegistry()
