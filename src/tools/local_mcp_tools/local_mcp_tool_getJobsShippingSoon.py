from src.tools.sql_tools import get_jobs_shipping_soon


def oa_get_jobs_shipping_soon(days_ahead: int = 30):
    """Get jobs shipping within N days."""
    return get_jobs_shipping_soon(days_ahead)
