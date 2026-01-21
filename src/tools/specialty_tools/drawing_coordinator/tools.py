"""
Drawing Coordinator Tools - Agent Executors

These functions send commands to the user's connected agent
to perform drawing coordinator operations locally.

All tools are ASYNC - they communicate with the agent via WebSocket.
"""
from typing import Optional

from src.utils.agent_utils import agent_registry
from src.tools.auth import UserService


# =============================================================================
# Helper Functions
# =============================================================================

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
    if agent_registry.is_connected(email_username):
        return email_username
    
    # Also try with domain suffix (e.g., tylere.METALSFAB)
    for agent_info in agent_registry.list_agents():
        agent_username = agent_info['username'].lower()
        if agent_username.startswith(email_username):
            return agent_info['username']
    
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
        return None, {
            "error": "No agent connected for your account. Please ensure the Toolbox Agent is running."
        }
    
    agent_error = _check_agent_connected(username)
    if agent_error:
        return None, agent_error
    
    return username, None


# =============================================================================
# Transmittal Processing Tools
# =============================================================================

async def oa_dc_scan_downloads_for_transmittals(
    job_number: Optional[str] = None,
    minutes_ago: int = 15,
    user_id: int = None
) -> dict:
    """
    Scan Downloads folder for recent transmittal ZIP files.

    Use after manually downloading from cloud links (SharePoint, WeTransfer, etc.)
    to find transmittals ready for processing.

    Args:
        job_number: Optional filter - only return files matching this job
        minutes_ago: Look at files modified in last N minutes (default 15, max 120)
        user_id: Injected server-side

    Returns:
        Dict containing:
            - success: bool
            - downloads_folder: path scanned
            - files_found: list of detected transmittal ZIPs with metadata
            - ready_count: number ready for processing
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error

    try:
        result = await agent_registry.send_command(
            username=username,
            module="drawing_coordinator",
            action="scan_downloads_for_transmittals",
            params={
                "job_number": job_number,
                "minutes_ago": minutes_ago
            },
            timeout=30.0
        )

        if result.get("success"):
            return {
                "success": True,
                "downloads_folder": result.get("downloads_folder"),
                "time_window_minutes": result.get("time_window_minutes"),
                "files_found": result.get("files_found", []),
                "total_found": result.get("total_found", 0),
                "ready_count": result.get("ready_count", 0)
            }
        else:
            return {"error": result.get("error", "Scan failed")}

    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": f"Failed to scan downloads: {str(e)}"}


async def oa_dc_process_transmittal(
    zip_path: str,
    output_path: Optional[str] = None,
    job_number: Optional[str] = None,
    distribute_data: bool = True,
    user_id: int = None
) -> dict:
    """
    Process a transmittal ZIP file through the full pipeline.
    
    Extracts, classifies, organizes, and optionally distributes files
    from a steel fabrication transmittal package.
    
    Args:
        zip_path: Full path to the input ZIP file
        output_path: Directory for output (default: ~/Desktop/DrawingCoordinatorMCP/Output)
        job_number: Optional 4-digit job number. Auto-detected if not provided.
        distribute_data: Whether to distribute files to network destinations (default: True)
        user_id: Injected server-side
        
    Returns:
        Dict containing:
            - success: bool
            - job_data: dict with job info, file counts, distribution results
            - logs: summarized log entries
            - status: final status message
            - error: error message if failed
            - log_file: path to detailed log file
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="drawing_coordinator",
            action="process_transmittal",
            params={
                "zip_path": zip_path,
                "output_path": output_path,
                "job_number": job_number,
                "distribute_data": distribute_data
            },
            timeout=300.0  # 5 minutes - transmittal processing can take a while
        )
        
        if result.get("success"):
            return {
                "success": True,
                "job_data": result.get("job_data", {}),
                "logs": result.get("logs", {}),
                "log_file": result.get("log_file"),
                "status": result.get("status", "Complete")
            }
        else:
            return {"error": result.get("error", "Unknown error during processing")}
            
    except TimeoutError:
        return {
            "error": "Processing timed out. The transmittal may be very large. Check the agent logs for status."
        }
    except Exception as e:
        return {"error": f"Failed to process transmittal: {str(e)}"}


async def oa_dc_get_default_output_path(user_id: int = None) -> dict:
    """
    Get the default output path for transmittal processing.
    
    Useful for showing the user where files will be saved.
    
    Args:
        user_id: Injected server-side
        
    Returns:
        Dict with path and whether it exists
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="drawing_coordinator",
            action="get_default_output_path",
            params={},
            timeout=15.0
        )
        
        if result.get("success"):
            return {
                "path": result.get("path"),
                "exists": result.get("exists", False)
            }
        else:
            return {"error": result.get("error", "Failed to get output path")}
            
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "oa_dc_scan_downloads_for_transmittals",
    "oa_dc_process_transmittal",
    "oa_dc_get_default_output_path",
]
