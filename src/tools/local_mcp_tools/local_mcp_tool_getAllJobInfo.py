from src.tools.sql_tools import get_jobs


def oa_get_jobs():
    """OpenAI tool wrapper for get_jobs."""
    return get_jobs()


__all__ = ['oa_get_jobs']
