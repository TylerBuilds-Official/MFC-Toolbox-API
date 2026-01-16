"""
Filesystem connector tools for LLM.

These tools allow the LLM to read/write files on the user's computer
through their connected agent, with permission checking.

These are ASYNC tools - they need to be awaited.
"""
from typing import Optional

from src.utils.agent_utils import agent_registry
from src.utils.connector_utils import (
    get_connector_config,
    get_allowed_folders,
    check_path_permission,
)
from src.tools.auth import UserService


def _get_username_from_user_id(user_id: int) -> Optional[str]:
    """
    Get the Windows username for a user by matching their email prefix
    to connected agents.
    
    Email: tylere@MetalsFab.com -> username: tylere
    """
    user = UserService.get_user_by_id(user_id)
    if not user or not user.email:
        return None
    
    # Extract username from email (part before @)
    email_username = user.email.split('@')[0].lower()
    
    # Check if agent is connected with this username
    # Agent registers with Windows username which should match email prefix
    if agent_registry.is_connected(email_username):
        return email_username
    
    # Also try with domain suffix (e.g., tylere.METALSFAB)
    # Some Windows setups include domain in username
    for agent_info in agent_registry.list_agents():
        agent_username = agent_info['username'].lower()
        # Match if email username is prefix of Windows username
        if agent_username.startswith(email_username):
            return agent_info['username']
    
    return None


def _check_connector_and_permission(user_id: int, path: str, action: str) -> dict | None:
    """
    Check if filesystem connector is enabled and user has permission.
    
    Returns None if OK, or error dict if not permitted.
    """
    # Check if connector is enabled
    config = get_connector_config(str(user_id), "filesystem")
    if not config or not config.enabled:
        return {
            "error": "Filesystem connector is not enabled. Please enable it in Settings > Connectors."
        }
    
    # Check path permission
    if not check_path_permission(str(user_id), path, action):
        allowed = get_allowed_folders(str(user_id))
        allowed_paths = [f.path for f in allowed]
        return {
            "error": f"Access denied: '{path}' is not in your allowed folders or lacks '{action}' permission.",
            "allowed_folders": allowed_paths,
            "hint": "Add this folder in Settings > Connectors, or use a path under an existing allowed folder."
        }
    
    return None


def _check_agent_connected(username: str) -> dict | None:
    """
    Check if user's agent is connected.
    Returns None if connected, or error dict if not.
    """
    if not agent_registry.is_connected(username):
        return {
            "error": "Agent not connected. Please ensure the Toolbox Agent is running on your computer.",
            "hint": "The agent should start automatically when you log in. Contact IT if the problem persists."
        }
    return None


# =============================================================================
# Async Tool Executors
# =============================================================================

async def oa_fs_list_directory(path: str, user_id: int = None) -> dict:
    """
    List contents of a directory on the user's computer.
    
    Args:
        path: Directory path to list
        user_id: Injected server-side
        
    Returns:
        Dict with entries list or error
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    # Get username by matching email to connected agent
    username = _get_username_from_user_id(user_id)
    if not username:
        return {"error": "No agent connected for your account. Please ensure the Toolbox Agent is running."}
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    # Check agent connected
    agent_error = _check_agent_connected(username)
    if agent_error:
        return agent_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="list_directory",
            params={"path": path},
            timeout=15.0
        )
        if result.get("success"):
            return {
                "path": path,
                "entries": result.get("entries", []),
                "count": result.get("count", len(result.get("entries", [])))
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time. Please try again."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_read_file(path: str, user_id: int = None) -> dict:
    """
    Read contents of a file on the user's computer.
    
    Args:
        path: File path to read
        user_id: Injected server-side
        
    Returns:
        Dict with file content or error
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    username = _get_username_from_user_id(user_id)
    if not username:
        return {"error": "No agent connected for your account. Please ensure the Toolbox Agent is running."}
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    # Check agent connected
    agent_error = _check_agent_connected(username)
    if agent_error:
        return agent_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="read_file",
            params={"path": path},
            timeout=30.0
        )
        if result.get("success"):
            return {
                "path": path,
                "content": result.get("content", ""),
                "size": result.get("size", 0),
                "encoding": result.get("encoding", "utf-8")
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time. The file may be too large."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_write_file(path: str, content: str, user_id: int = None) -> dict:
    """
    Write content to a file on the user's computer.
    
    Args:
        path: File path to write
        content: Content to write
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    username = _get_username_from_user_id(user_id)
    if not username:
        return {"error": "No agent connected for your account. Please ensure the Toolbox Agent is running."}
    
    # Check connector and permissions (need write permission)
    perm_error = _check_connector_and_permission(user_id, path, "write")
    if perm_error:
        return perm_error
    
    # Check agent connected
    agent_error = _check_agent_connected(username)
    if agent_error:
        return agent_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="write_file",
            params={"path": path, "content": content},
            timeout=30.0
        )
        if result.get("success"):
            return {
                "path": path,
                "bytes_written": result.get("bytes_written", len(content)),
                "message": f"Successfully wrote to {path}"
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_delete_file(path: str, user_id: int = None) -> dict:
    """
    Delete a file on the user's computer.
    
    Args:
        path: File path to delete
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    username = _get_username_from_user_id(user_id)
    if not username:
        return {"error": "No agent connected for your account. Please ensure the Toolbox Agent is running."}
    
    # Check connector and permissions (need delete permission)
    perm_error = _check_connector_and_permission(user_id, path, "delete")
    if perm_error:
        return perm_error
    
    # Check agent connected
    agent_error = _check_agent_connected(username)
    if agent_error:
        return agent_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="delete_file",
            params={"path": path},
            timeout=15.0
        )
        if result.get("success"):
            return {
                "path": path,
                "deleted": True,
                "message": f"Successfully deleted {path}"
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


def oa_fs_get_allowed_folders(user_id: int = None) -> dict:
    """
    Get the list of folders the user has allowed access to.
    Useful for the LLM to know what paths are available.
    
    Note: This one is NOT async - it doesn't need the agent.
    
    Args:
        user_id: Injected server-side
        
    Returns:
        Dict with allowed folders and their permissions
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    # Check if connector is enabled
    config = get_connector_config(str(user_id), "filesystem")
    if not config or not config.enabled:
        return {
            "enabled": False,
            "folders": [],
            "message": "Filesystem connector is not enabled."
        }
    
    # Get allowed folders
    folders = get_allowed_folders(str(user_id))
    
    # Also check if agent is connected
    username = _get_username_from_user_id(user_id)
    agent_connected = username is not None
    
    return {
        "enabled": True,
        "agent_connected": agent_connected,
        "folders": [
            {
                "path": f.path,
                "can_read": f.can_read,
                "can_write": f.can_write,
                "can_delete": f.can_delete
            }
            for f in folders
        ],
        "count": len(folders)
    }


# Mark which tools are async for the dispatcher
ASYNC_TOOLS = {
    'fs_list_directory',
    'fs_read_file',
    'fs_write_file',
    'fs_delete_file',
}


__all__ = [
    'oa_fs_list_directory',
    'oa_fs_read_file', 
    'oa_fs_write_file',
    'oa_fs_delete_file',
    'oa_fs_get_allowed_folders',
    'ASYNC_TOOLS',
]
