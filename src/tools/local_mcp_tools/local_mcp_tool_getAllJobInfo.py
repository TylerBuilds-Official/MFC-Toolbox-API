from src.tools.sql_tools.get_jobs import get_jobs


def oa_get_jobs():
    """OpenAI tool wrapper for get_jobs."""
    return get_jobs()


__all__ = ['oa_get_jobs']
