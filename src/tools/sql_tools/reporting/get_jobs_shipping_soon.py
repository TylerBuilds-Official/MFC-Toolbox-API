"""
Get jobs shipping within a specified number of days from ScheduleShare.

Retrieves jobs with upcoming ship dates for deadline tracking.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_jobs_shipping_soon(days_ahead: int = 30) -> list[dict]:
    """
    Get jobs shipping within N days.
    
    Calls ScheduleShare.Toolbox_GetJobsShippingSoon stored procedure.
    
    Args:
        days_ahead: Number of days to look ahead (default 30)
        
    Returns:
        List of dicts with job information for jobs shipping soon
    """
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC ScheduleShare.Toolbox_GetJobsShippingSoon @DaysAhead = ?",
            (days_ahead,)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        # Convert to list of dicts
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            results.append(record)
        
        return results


__all__ = ['get_jobs_shipping_soon']
