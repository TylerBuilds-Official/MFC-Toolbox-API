from src.tools.sql_tools.get_job_info import get_job_info


def oa_get_job_info(job_number: int | str):
    """OpenAI tool wrapper for get_job_info."""
    return get_job_info(job_number)


__all__ = ['oa_get_job_info']
