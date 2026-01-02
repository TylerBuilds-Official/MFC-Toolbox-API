from src.tools.sql_tools import get_active_jobs


def oa_get_active_jobs(include_on_hold: bool = False):
    """Get all active jobs, optionally including on-hold jobs."""
    return get_active_jobs(include_on_hold)
