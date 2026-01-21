"""
Document Creation Tools - Agent Executors

These functions send commands to the user's connected agent
to create documents locally.

Internal tools for AI orchestration - not exposed in toolbox UI.
All tools are ASYNC - they communicate with the agent via WebSocket.
"""
from typing import Optional, Any

from src.utils.agent_utils import agent_registry
from src.tools.auth import UserService


# =============================================================================
# Helper Functions
# =============================================================================

def _get_username_from_user_id(user_id: int) -> Optional[str]:
    """
    Get the Windows username for a user by matching their email prefix
    to connected agents.
    """
    user = UserService.get_user_by_id(user_id)
    if not user or not user.email:
        return None
    
    email_username = user.email.split('@')[0].lower()
    
    if agent_registry.is_connected(email_username):
        return email_username
    
    for agent_info in agent_registry.list_agents():
        agent_username = agent_info['username'].lower()
        if agent_username.startswith(email_username):
            return agent_info['username']
    
    return None


def _get_user_and_check_agent(user_id: int) -> tuple[Optional[str], Optional[dict]]:
    """
    Common setup: get username and check agent connection.
    """
    if user_id is None:
        return None, {"error": "User context not available"}
    
    username = _get_username_from_user_id(user_id)
    if not username:
        return None, {
            "error": "No agent connected for your account. Please ensure the Toolbox Agent is running."
        }
    
    if not agent_registry.is_connected(username):
        return None, {
            "error": "Agent not connected. Please ensure the Toolbox Agent is running on your computer."
        }
    
    return username, None


# =============================================================================
# HTML Report Tools
# =============================================================================

async def oa_doc_create_html_report(
    template_name: str,
    data: Optional[dict[str, Any]] = None,
    title: Optional[str] = None,
    output_filename: Optional[str] = None,
    user_id: int = None
) -> dict:
    """
    Create an HTML report from a template with injected data.

    Args:
        template_name: Template file name (e.g., "base_report.html")
        data: Dictionary of data to inject into the template (optional, defaults to empty)
        title: Report title (optional)
        output_filename: Output filename (optional, auto-generated if not provided)
        user_id: Injected server-side
        
    Returns:
        Dict with success status, file path, and metadata
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    # Default data to empty dict if not provided
    if data is None:
        data = {}
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="document_creation",
            action="create_html_report",
            params={
                "template_name": template_name,
                "data": data,
                "title": title,
                "output_filename": output_filename
            },
            timeout=30.0
        )
        
        if result.get("success"):
            return {
                "success": True,
                "file_path": result.get("file_path"),
                "filename": result.get("filename"),
                "template_used": result.get("template_used")
            }
        else:
            return {"error": result.get("error", "Failed to create report")}
            
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": f"Failed to create report: {str(e)}"}


async def oa_doc_save_raw_html(
    content: str,
    output_filename: str,
    user_id: int = None
) -> dict:
    """
    Save raw HTML content to a file.
    
    Use when the AI generates complete HTML content directly.
    
    Args:
        content: Complete HTML string
        output_filename: Output filename
        user_id: Injected server-side
        
    Returns:
        Dict with success status and file path
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="document_creation",
            action="save_raw_html",
            params={
                "content": content,
                "output_filename": output_filename
            },
            timeout=30.0
        )
        
        if result.get("success"):
            return {
                "success": True,
                "file_path": result.get("file_path"),
                "filename": result.get("filename")
            }
        else:
            return {"error": result.get("error", "Failed to save HTML")}
            
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": f"Failed to save HTML: {str(e)}"}


async def oa_doc_list_report_templates(user_id: int = None) -> dict:
    """
    List available HTML report templates and get skill documentation.

    Returns templates AND the skill guide with data formatting examples.
    Always call this before create_html_report.

    Args:
        user_id: Injected server-side

    Returns:
        Dict with list of templates, descriptions, and skill guide
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error

    try:
        result = await agent_registry.send_command(
            username=username,
            module="document_creation",
            action="list_report_templates",
            params={},
            timeout=15.0
        )

        if result.get("success"):
            return {
                "success": True,
                "templates": result.get("templates", []),
                "count": result.get("count", 0),
                "skill_guide": result.get("skill_guide")
            }
        else:
            return {"error": result.get("error", "Failed to list templates")}
            
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


async def oa_doc_get_report_skill(user_id: int = None) -> dict:
    """
    Get the HTML report skill documentation for AI guidance.
    
    Args:
        user_id: Injected server-side
        
    Returns:
        Dict with skill markdown content
    """
    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="document_creation",
            action="get_report_skill",
            params={},
            timeout=15.0
        )
        
        if result.get("success"):
            return {
                "success": True,
                "skill_content": result.get("skill_content")
            }
        else:
            return {"error": result.get("error", "Skill not found")}
            
    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


async def oa_doc_get_default_output_path(user_id: int = None) -> dict:
    """
    Get the default output path for documents.
    
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
            module="document_creation",
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
    "oa_doc_create_html_report",
    "oa_doc_save_raw_html",
    "oa_doc_list_report_templates",
    "oa_doc_get_report_skill",
    "oa_doc_get_default_output_path",
]
