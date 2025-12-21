"""
Retrieves all jobs from the database.
"""

def get_jobs() -> dict:
    """
    Retrieves all jobs from the database using a stored procedure.

    Returns:
        A dictionary containing all job information keyed by JobNumber,
        or an error message if no jobs are found.
    """
    from src.tools.sql_tools.mysql_pool import get_mysql_connection
    
    with get_mysql_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("CALL MFC_ToolBox_GetAllJobInfo();")
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
