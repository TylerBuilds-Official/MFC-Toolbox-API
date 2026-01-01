from src.tools.sql_tools import get_ot_hours_all_jobs


def oa_get_ot_hours_all_jobs(start_date: str = None, end_date: str = None):
    """Get OT hours across all jobs."""
    return get_ot_hours_all_jobs(start_date, end_date)
