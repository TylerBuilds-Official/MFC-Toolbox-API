"""
Get comprehensive details for a specific job from ScheduleShare.

Retrieves detailed information about a single job by job number.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_job_details(job_number: str) -> list[dict]:
    """
    Get comprehensive details for a specific job.
    
    Calls ScheduleShare.Toolbox_GetJobDetails stored procedure.
    
    Args:
        job_number: The job number to query
        
    Returns:
        List of dicts with detailed job information (typically single record)
    """
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC ScheduleShare.Toolbox_GetJobDetails @JobNumber = ?",
            (job_number,)
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


__all__ = ['get_job_details']
