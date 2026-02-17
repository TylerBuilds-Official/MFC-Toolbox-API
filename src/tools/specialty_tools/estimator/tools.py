"""
Estimator Tools — Agent Executors

Sends classification commands to the user's local agent.
Anthropic API key is injected server-side from environment.
"""
import os

from src.utils.agent_utils import agent_registry
from src.tools.specialty_tools.drawing_coordinator.tools import _get_user_and_check_agent


def _get_anthropic_key() -> str | None:
    """Get the Anthropic API key from server environment"""

    return os.environ.get("ANTHROPIC_API_KEY")


async def oa_est_classify_and_breakout(
        pdf_path: str,
        output_path: str | None = None,
        user_id: int = None ) -> dict:
    """Classify a construction plan PDF and split into per-discipline files"""

    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error

    api_key = _get_anthropic_key()
    if not api_key:
        return {"error": "Anthropic API key not configured on server"}

    try:
        result = await agent_registry.send_command(
            username=username,
            module="estimator",
            action="classify_and_breakout",
            params={
                "pdf_path": pdf_path,
                "anthropic_api_key": api_key,
                "output_path": output_path,
            },
            timeout=600.0,
        )

        if result.get("success"):
            return {
                "success":     True,
                "pdf_path":    result.get("pdf_path"),
                "page_count":  result.get("page_count"),
                "results":     result.get("results", []),
                "breakout":    result.get("breakout", {}),
                "output_path": result.get("output_path"),
                "timings":     result.get("timings", {}),
                "total_cost":  result.get("total_cost", 0.0),
            }
        else:
            return {"error": result.get("error", "Classification/breakout failed")}

    except TimeoutError:
        return {"error": "Classification timed out. Large PDFs may take several minutes."}
    except Exception as e:
        return {"error": f"Failed to classify and breakout PDF: {str(e)}"}


async def oa_est_get_default_output_path(user_id: int = None) -> dict:
    """Get the default output path for classification breakout files"""

    username, error = _get_user_and_check_agent(user_id)
    if error:
        return error

    try:
        result = await agent_registry.send_command(
            username=username,
            module="estimator",
            action="get_default_output_path",
            params={},
            timeout=15.0,
        )

        if result.get("success"):
            return {
                "path":   result.get("path"),
                "exists": result.get("exists", False),
            }
        else:
            return {"error": result.get("error", "Failed to get output path")}

    except TimeoutError:
        return {"error": "Agent did not respond in time."}
    except Exception as e:
        return {"error": str(e)}


__all__ = [
    "oa_est_classify_and_breakout",
    "oa_est_get_default_output_path",
]
