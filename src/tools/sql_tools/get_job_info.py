"""
Retrieves job information for a specific job number.
"""

def get_job_info(job_number: int | str) -> dict:
    """
    Retrieves job information for a specific job number from the database 
    using a stored procedure.

    Args:
        job_number: The job number for which to retrieve information.

    Returns:
        A dictionary containing job information keyed by JobNumber,
        or an error message if no jobs are found.
    """
    from src.tools.sql_tools.pool import get_connection
    
    if isinstance(job_number, str):
        job_number = int(job_number)

    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"CALL MFC_ToolBox_GetJobInfo({job_number});")
            data = cursor.fetchall()
            
            # Consume any remaining result sets from stored procedure
            while cursor.nextset():
                pass

    if data is None:
        return {"message": "No jobs found, SQL query returned None"}

    model_data = {}
    for job in data:
        model_data[job['JobNumber']] = job

    return model_data
