"""
Unified Job Information Retrieval

Merges data from:
- MySQL (Strider): Tekla production data (TotalPieces, TotalWeight, StartDate)
- SQL Server (ScheduleShare): Project management data (Hours, Dates, Financial, Status)

Returns a consolidated view with the best data from each source.
"""
from src.tools.sql_tools.pools import get_mysql_connection, get_voltron_connection


# =============================================================================
# PM Name Mapping
# =============================================================================

PM_NAME_MAP = {
    'Blake':     'Blake Reed',
    'Conrad':    'Conrad Schmidt',
    'Evan':      'Evan Weaver',
    'James':     'James',
    'Joe':       'Joe Lenoue',
    'Ken':       'Ken Bastine',
    'Matt Leon': 'Matt Leon',
    'Quintin':   'Quintin Porterfield',
    'Raymond':   'Raymond Rodriguez',
}


def _format_pm_name(name: str | None) -> str | None:
    """Map PM first name to full name."""
    if not name:
        return None
    trimmed = name.strip()
    return PM_NAME_MAP.get(trimmed, trimmed)


# =============================================================================
# Status Code Mapping
# =============================================================================

STATUS_MAP = {
    0: "Active",
    1: "Complete",
    2: "Modified",
    3: "On Hold",
}


# =============================================================================
# Data Fetchers
# =============================================================================

def _fetch_strider_data(job_number: int) -> dict | None:
    """
    Fetch job data from MySQL (Strider/Tekla).
    
    Unique fields: JobName (cleaner), StartDate, Contractor (fuller), TotalPieces, TotalWeight
    """
    try:
        with get_mysql_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"CALL MFC_ToolBox_GetJobInfo({job_number});")
                rows = cursor.fetchall()
                
                while cursor.nextset():
                    pass
                
                return rows[0] if rows else None
    except Exception as e:
        print(f"[get_job_info] Strider fetch error: {e}")
        return None


def _fetch_scheduleshare_data(job_number: int) -> dict | None:
    """
    Fetch job data from SQL Server (ScheduleShare).
    
    Primary source for: Hours, Dates, Financial, People, Status
    """
    try:
        with get_voltron_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "EXEC ScheduleShare.Toolbox_GetJobDetails @JobNumber = ?",
                (job_number,)
            )
            
            columns = [col[0] for col in cursor.description]
            row     = cursor.fetchone()
            
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return dict(zip(columns, row)) if row else None
    except Exception as e:
        print(f"[get_job_info] ScheduleShare fetch error: {e}")
        return None


# =============================================================================
# Merge Logic
# =============================================================================

def _merge_job_data(strider: dict | None, scheduleshare: dict | None) -> dict:
    """
    Merge data from both sources into unified response.
    
    Priority:
    - Strider: JobName, StartDate, Contractor, TotalPieces, TotalWeight
    - ScheduleShare: Everything else (hours, dates, financial, people, status)
    """
    s  = strider or {}
    ss = scheduleshare or {}
    
    # Calculate HoursRemaining if we have the data
    hours_used  = ss.get("HoursUsed")
    total_hours = ss.get("TotalHours")
    hours_remaining = None
    if hours_used is not None and total_hours is not None:
        hours_remaining = round(float(total_hours) - float(hours_used), 2)
    
    # Map status code to readable string
    status_code = ss.get("StatusCode")
    status      = STATUS_MAP.get(status_code, "Unknown") if status_code is not None else None
    
    # Prefer Strider's fuller contractor name, fallback to ScheduleShare
    contractor = s.get("Contractor") or ss.get("GeneralContractor")
    
    # Build merged result
    merged = {
        # Core Identity
        "JobNumber":         s.get("JobNumber") or ss.get("JobNumber"),
        "JobName":           s.get("JobName"),                           # Strider (cleaner)
        "Status":            status,
        
        # People
        "ProjectManager":    _format_pm_name(ss.get("ProjectManager")),
        "Detailer":          ss.get("Detailer"),
        "Erector":           ss.get("Erector"),
        "GeneralContractor": contractor,
        
        # Dates
        "StartDate":         s.get("StartDate"),                         # Strider only
        "TargetDelivery":    ss.get("TargetDelivery"),
        "ErectDate":         ss.get("ErectDate"),
        
        # Hours
        "HoursUsed":         ss.get("HoursUsed"),
        "HoursRemaining":    hours_remaining,                            # Calculated
        "TotalHours":        ss.get("TotalHours"),
        
        # Production (Tekla actuals - Strider)
        "TotalPieces":       s.get("TotalPieces"),
        "TotalWeight":       s.get("TotalWeight"),
        "WeightShipped":     ss.get("WeightShipped"),
        
        # Financial
        "ContractAmount":    ss.get("ContractAmount"),
        "CostsToDate":       ss.get("CostsToDate"),
        
        # Status
        "SteelStatus":       ss.get("SteelStatus"),
        "Notes":             ss.get("Notes"),
    }
    
    # Filter out None/empty values
    return {k: v for k, v in merged.items() if v is not None and v != ""}


# =============================================================================
# Public API
# =============================================================================

def get_job_info(job_number: int | str) -> dict:
    """
    Get comprehensive job information from all available sources.
    
    Merges data from:
    - Strider (MySQL): Tekla production data
    - ScheduleShare (SQL Server): Project management data
    
    Args:
        job_number: The job number to retrieve
        
    Returns:
        Dict with merged job data, or error message if not found
    """
    if isinstance(job_number, str):
        job_number = int(job_number)
    
    # Fetch from both sources
    strider_data       = _fetch_strider_data(job_number)
    scheduleshare_data = _fetch_scheduleshare_data(job_number)
    
    # If neither source has data, return error
    if not strider_data and not scheduleshare_data:
        return {"error": f"Job {job_number} not found in any data source"}
    
    # Merge and return
    return _merge_job_data(strider_data, scheduleshare_data)


__all__ = ['get_job_info']
