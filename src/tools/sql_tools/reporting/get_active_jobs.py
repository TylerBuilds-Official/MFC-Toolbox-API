"""
Get all active jobs from ScheduleShare.

Retrieves active jobs with optional inclusion of on-hold jobs.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_active_jobs(include_on_hold: bool = False) -> list[dict]:
    """
    Get all active jobs.
    
    Calls ScheduleShare.Toolbox_GetActiveJobs stored procedure.
    
    Args:
        include_on_hold: Whether to include on-hold jobs (default False)
        
    Returns:
        List of dicts with job information (columns determined by stored procedure)
    """
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC ScheduleShare.Toolbox_GetActiveJobs @IncludeOnHold = ?",
            (1 if include_on_hold else 0,)
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


__all__ = ['get_active_jobs']
