from src.tools.sql_tools import get_ot_hours_by_job


def oa_get_ot_hours_by_job(job_number: str, start_date: str = None, end_date: str = None):
    """Get OT hours for a specific job, broken down by employee."""
    return get_ot_hours_by_job(job_number, start_date, end_date)
