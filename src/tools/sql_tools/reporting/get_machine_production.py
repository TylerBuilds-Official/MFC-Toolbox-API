"""
Get machine production data for charting.

Retrieves daily production counts (pieces processed, total weight) 
per CNC machine from FabTracker.ProductionLog.
"""
from src.tools.sql_tools.pools import get_voltron_connection


def get_machine_production(days_back: int = 30) -> list[dict]:
    """
    Get daily production metrics per machine.
    
    Calls FabTracker.MFC_Toolbox_GetMachineProduction stored procedure.
    
    Args:
        days_back: Number of days to look back (default 30)
        
    Returns:
        List of dicts with keys:
        - ProductionDate: date string
        - Machine: machine name
        - PiecesProcessed: count of pieces
        - TotalWeight: sum of weight in lbs
    """
    with get_voltron_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "EXEC FabTracker.MFC_Toolbox_GetMachineProduction @DaysBack = ?",
            (days_back,)
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


__all__ = ['get_machine_production']
