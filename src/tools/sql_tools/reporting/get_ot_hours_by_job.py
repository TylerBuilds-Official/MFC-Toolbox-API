"""
Get overtime hours breakdown by employee for a specific job.

Retrieves OT hours from ScheduleShare, broken down by employee,
for a given job number and date range.
"""
from datetime import date, timedelta
from typing import Optional

from src.tools.sql_tools.pools import get_voltron_connection


def get_ot_hours_by_job(
    job_number: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
    """
    Get OT hours for a specific job, broken down by employee.
    
    Calls ScheduleShare.GetOTHoursByJob stored procedure.
    
    Args:
        job_number: The job number to query
        start_date: Start date (YYYY-MM-DD format), defaults to 7 days ago
        end_date: End date (YYYY-MM-DD format), defaults to today
        
    Returns:
        List of dicts with keys:
        - CEMPID: Employee ID
        - CFIRSTNAME: First name
        - CLASTNAME: Last name
        - JobNumber: Job number
        - TotalOTHours: Total overtime hours
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
            "EXEC ScheduleShare.Toolbox_GetOTHoursByJob @JobNumber = ?, @StartDate = ?, @EndDate = ?",
            (job_number, start_date, end_date)
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


__all__ = ['get_ot_hours_by_job']
