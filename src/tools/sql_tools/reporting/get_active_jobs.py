"""
Get all active jobs from ScheduleShare.

Retrieves currently active jobs with project details.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_active_jobs() -> list[dict]:
    """
    Get all active jobs.

    Calls ScheduleShare.Toolbox_GetActiveJobs stored procedure.

    Returns:
        List of dicts with job information (columns determined by stored procedure)
    """
    with get_voltron_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("EXEC ScheduleShare.Toolbox_GetActiveJobs")

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