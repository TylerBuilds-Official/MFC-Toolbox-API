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


def _get_user_and_check_agent(user_id: int) -> tuple[Optional[str], Optional[dict]]:
    """
    Common setup: get username and check agent connection.
    
    Returns:
        (username, None) if OK
        (None, error_dict) if error
    """
    if user_id is None:
        return None, {"error": "User context not available"}
    
    username = _get_username_from_user_id(user_id)
    if not username:
        return None, {"error": "No agent connected for your account. Please ensure the Toolbox Agent is running."}
    
    agent_error = _check_agent_connected(username)
    if agent_error:
        return None, agent_error
    
    return username, None


# =============================================================================
# Directory Operations
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
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
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


async def oa_fs_create_directory(path: str, parents: bool = True, user_id: int = None) -> dict:
    """
    Create a directory on the user's computer.
    
    Args:
        path: Directory path to create
        parents: If True, create parent directories as needed (default True)
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions (need write permission)
    perm_error = _check_connector_and_permission(user_id, path, "write")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="create_directory",
            params={"path": path, "parents": parents},
            timeout=15.0
        )
        if result.get("success"):
            return {
                "path": result.get("path", path),
                "created": result.get("created", True),
                "message": result.get("message", f"Directory created: {path}")
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_directory_tree(
    path: str,
    max_depth: int = 5,
    include_files: bool = True,
    include_hidden: bool = False,
    user_id: int = None
) -> dict:
    """
    Get a recursive tree view of a directory on the user's computer.
    
    Args:
        path: Root directory path
        max_depth: Maximum recursion depth (default 5, max 10)
        include_files: Include files in output (default True)
        include_hidden: Include hidden files/folders (default False)
        user_id: Injected server-side
        
    Returns:
        Dict with nested tree structure or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="directory_tree",
            params={
                "path": path,
                "max_depth": max_depth,
                "include_files": include_files,
                "include_hidden": include_hidden
            },
            timeout=30.0  # Tree can take longer
        )
        if result.get("success"):
            return {
                "path": path,
                "tree": result.get("tree", {}),
                "file_count": result.get("file_count", 0),
                "directory_count": result.get("directory_count", 0)
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time. Try reducing max_depth."}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# File Operations
# =============================================================================

async def oa_fs_read_file(path: str, user_id: int = None) -> dict:
    """
    Read contents of a file on the user's computer.
    
    Args:
        path: File path to read
        user_id: Injected server-side
        
    Returns:
        Dict with file content or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
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
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions (need write permission)
    perm_error = _check_connector_and_permission(user_id, path, "write")
    if perm_error:
        return perm_error
    
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


async def oa_fs_edit_file(
    path: str,
    old_text: str,
    new_text: str,
    user_id: int = None
) -> dict:
    """
    Edit a file by replacing text. The old_text must appear exactly once in the file.
    
    Args:
        path: File path to edit
        old_text: Text to find and replace (must be unique in file)
        new_text: Replacement text (can be empty to delete)
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions (need write permission)
    perm_error = _check_connector_and_permission(user_id, path, "write")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="edit_file",
            params={
                "path": path,
                "old_text": old_text,
                "new_text": new_text
            },
            timeout=30.0
        )
        if result.get("success"):
            return {
                "path": result.get("path", path),
                "old_text_length": result.get("old_text_length", len(old_text)),
                "new_text_length": result.get("new_text_length", len(new_text)),
                "message": result.get("message", "File edited successfully")
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
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions (need delete permission)
    perm_error = _check_connector_and_permission(user_id, path, "delete")
    if perm_error:
        return perm_error
    
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


async def oa_fs_copy_file(source: str, destination: str, user_id: int = None) -> dict:
    """
    Copy a file to a new location on the user's computer.
    
    Args:
        source: Source file path
        destination: Destination path (can be file or directory)
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check permissions: need read on source, write on destination
    perm_error = _check_connector_and_permission(user_id, source, "read")
    if perm_error:
        return perm_error
    
    perm_error = _check_connector_and_permission(user_id, destination, "write")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="copy_file",
            params={"source": source, "destination": destination},
            timeout=60.0  # Copies can take longer for large files
        )
        if result.get("success"):
            return {
                "source": result.get("source", source),
                "destination": result.get("destination", destination),
                "size": result.get("size"),
                "message": f"Successfully copied to {result.get('destination', destination)}"
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time. The file may be very large."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_move_file(source: str, destination: str, user_id: int = None) -> dict:
    """
    Move or rename a file or directory on the user's computer.
    
    Args:
        source: Source path (file or directory)
        destination: Destination path
        user_id: Injected server-side
        
    Returns:
        Dict with success status or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check permissions: need delete on source (it's being moved), write on destination
    perm_error = _check_connector_and_permission(user_id, source, "delete")
    if perm_error:
        return perm_error
    
    perm_error = _check_connector_and_permission(user_id, destination, "write")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="move_file",
            params={"source": source, "destination": destination},
            timeout=60.0
        )
        if result.get("success"):
            return {
                "source": result.get("source", source),
                "destination": result.get("destination", destination),
                "is_dir": result.get("is_dir", False),
                "message": f"Successfully moved to {result.get('destination', destination)}"
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Search & Info Operations
# =============================================================================

async def oa_fs_search_files(
    path: str,
    pattern: str,
    max_results: int = 100,
    include_hidden: bool = False,
    user_id: int = None
) -> dict:
    """
    Search for files matching a pattern on the user's computer.
    
    Args:
        path: Directory to search in
        pattern: Search pattern (glob like *.py or substring)
        max_results: Maximum results to return (default 100)
        include_hidden: Include hidden files (default False)
        user_id: Injected server-side
        
    Returns:
        Dict with matching files or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="search_files",
            params={
                "path": path,
                "pattern": pattern,
                "max_results": max_results,
                "include_hidden": include_hidden
            },
            timeout=60.0  # Search can take a while
        )
        if result.get("success"):
            return {
                "path": path,
                "pattern": pattern,
                "matches": result.get("matches", []),
                "count": result.get("count", 0),
                "truncated": result.get("truncated", False)
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time. Try a more specific path or pattern."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_get_file_info(path: str, user_id: int = None) -> dict:
    """
    Get detailed info about a file or directory on the user's computer.
    
    Args:
        path: Path to file or directory
        user_id: Injected server-side
        
    Returns:
        Dict with file info (name, size, dates, type) or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="get_file_info",
            params={"path": path},
            timeout=15.0
        )
        if result.get("success"):
            return {
                "path": result.get("path", path),
                "name": result.get("name"),
                "is_file": result.get("is_file"),
                "is_dir": result.get("is_dir"),
                "size": result.get("size"),
                "created": result.get("created"),
                "modified": result.get("modified"),
                "accessed": result.get("accessed")
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


async def oa_fs_file_exists(path: str, user_id: int = None) -> dict:
    """
    Check if a file or directory exists on the user's computer.
    
    Args:
        path: Path to check
        user_id: Injected server-side
        
    Returns:
        Dict with exists status and type or error
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Check connector and permissions
    perm_error = _check_connector_and_permission(user_id, path, "read")
    if perm_error:
        return perm_error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="filesystem",
            action="file_exists",
            params={"path": path},
            timeout=15.0
        )
        if result.get("success"):
            return {
                "path": result.get("path", path),
                "exists": result.get("exists", False),
                "is_file": result.get("is_file"),
                "is_dir": result.get("is_dir")
            }
        else:
            return {"error": result.get("error", "Unknown error")}
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Non-Async Tools (don't need agent)
# =============================================================================

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


# =============================================================================
# Exports
# =============================================================================

# Mark which tools are async for the dispatcher
ASYNC_TOOLS = {
    'fs_list_directory',
    'fs_create_directory',
    'fs_directory_tree',
    'fs_read_file',
    'fs_write_file',
    'fs_edit_file',
    'fs_delete_file',
    'fs_copy_file',
    'fs_move_file',
    'fs_search_files',
    'fs_get_file_info',
    'fs_file_exists',
}


__all__ = [
    # Directory operations
    'oa_fs_list_directory',
    'oa_fs_create_directory',
    'oa_fs_directory_tree',
    # File operations
    'oa_fs_read_file',
    'oa_fs_write_file',
    'oa_fs_edit_file',
    'oa_fs_delete_file',
    'oa_fs_copy_file',
    'oa_fs_move_file',
    # Search & info
    'oa_fs_search_files',
    'oa_fs_get_file_info',
    'oa_fs_file_exists',
    # Non-async
    'oa_fs_get_allowed_folders',
    # Metadata
    'ASYNC_TOOLS',
]
