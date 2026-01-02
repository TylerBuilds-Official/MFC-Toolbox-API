from src.tools.sql_tools import get_jobs_by_pm


def oa_get_jobs_by_pm(pm_name: str, active_only: bool = True):
    """Get all jobs for a specific Project Manager."""
    return get_jobs_by_pm(pm_name, active_only)
