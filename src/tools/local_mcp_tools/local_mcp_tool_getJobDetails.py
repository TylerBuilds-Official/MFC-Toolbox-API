from src.tools.sql_tools import get_job_details


def oa_get_job_details(job_number: str):
    """Get comprehensive details for a specific job."""
    return get_job_details(job_number)
