"""
Get overtime hours summary across all jobs.

Retrieves OT hours from ScheduleShare, aggregated by job,
for a given date range.
"""
from datetime import date, timedelta
from typing import Optional

from src.tools.sql_tools.pools import get_voltron_connection


def get_ot_hours_all_jobs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
    """
    Get OT hours across all jobs.
    
    Calls ScheduleShare.GetOTHoursAllJobs stored procedure.
    
    Args:
        start_date: Start date (YYYY-MM-DD format), defaults to 7 days ago
        end_date: End date (YYYY-MM-DD format), defaults to today
        
    Returns:
        List of dicts with keys:
        - JobNumber: Job number
        - TotalOTHours: Total overtime hours for the job
        - EmployeeCount: Number of employees with OT
        - DaysWorked: Number of days with OT
        - FirstDate: First date with OT
        - LastDate: Last date with OT
    """
    # Default date range: last 7 days
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.today() - timedelta(days=7)).isoformat()
    
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC ScheduleShare.GetOTHoursAllJobs @StartDate = ?, @EndDate = ?",
            (start_date, end_date)
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


__all__ = ['get_ot_hours_all_jobs']
