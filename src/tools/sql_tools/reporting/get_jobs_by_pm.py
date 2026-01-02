"""
Get all jobs for a specific Project Manager from ScheduleShare.

Retrieves jobs assigned to a PM with optional active-only filtering.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_jobs_by_pm(pm_name: str, active_only: bool = True) -> list[dict]:
    """
    Get all jobs for a specific Project Manager.
    
    Calls ScheduleShare.Toolbox_GetJobsByPM stored procedure.
    
    Args:
        pm_name: The Project Manager's name to query
        active_only: Whether to return only active jobs (default True)
        
    Returns:
        List of dicts with job information for the specified PM
    """
    if not pm_name or not pm_name.strip():
        return {
            "error": "Project Manager name is required"
        }

    pm_name = _validate_pm_name(pm_name)


    with get_voltron_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "EXEC ScheduleShare.Toolbox_GetJobsByPM @PMName = ?, @ActiveOnly = ?",
            (pm_name, 1 if active_only else 0)
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

def _validate_pm_name(pm_name: str):
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("EXEC ScheduleShare.Toolbox_GetProjectManagers")

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        # Clean up any remaining result sets
        while cursor.nextset():
            pass
        cursor.close()

        # Convert rows → dicts
        results = [dict(zip(columns, row)) for row in rows]

        for pm in results:
            if pm["ProjectManager"] in pm_name:
                return pm["ProjectManager"]

        return {"error": f"Project Manager '{pm_name}' not found."}


__all__ = ['get_jobs_by_pm']
