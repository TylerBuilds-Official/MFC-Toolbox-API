"""
Retrieves conversation projects.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_conversation_project(project_id: int, user_id: int = None) -> dict | None:
    """
    Retrieves a single conversation project by ID.
    
    Calls Toolbox_GetConversationProject stored procedure.
    
    Args:
        project_id: The project's ID
        user_id: Optional user ID for access verification
        
    Returns:
        Project dictionary or None if not found/no access
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetConversationProject @ProjectId = ?, @UserId = ?",
            (project_id, user_id)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if not row:
            return None
        
        # Parse permissions JSON if present
        permissions_raw = row[7]
        permissions = None
        if permissions_raw:
            try:
                permissions = json.loads(permissions_raw)
            except (json.JSONDecodeError, TypeError):
                permissions = None
        
        return {
            'id':                  row[0],
            'owner_id':            row[1],
            'name':                row[2],
            'description':         row[3],
            'color':               row[4],
            'custom_instructions': row[5],
            'project_type':        row[6],
            'permissions':         permissions,
            'created_at':          row[8],
            'updated_at':          row[9],
            'is_active':           row[10],
            'conversation_count':  row[11],
            'member_count':        row[12],
            'is_owner':            bool(row[13]),
            'user_role':           row[14],
        }


def get_conversation_projects_by_user(user_id: int) -> list[dict]:
    """
    Retrieves all conversation projects for a user (owned + shared with them).
    
    Calls Toolbox_GetConversationProjectsByUser stored procedure.
    
    Args:
        user_id: The user's ID
        
    Returns:
        List of project dictionaries, owned first then shared, ordered by UpdatedAt DESC
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetConversationProjectsByUser @UserId = ?",
            (user_id,)
        )
        
        rows = cursor.fetchall()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        results = []
        for row in rows:
            # Parse permissions JSON if present
            permissions_raw = row[7]
            permissions = None
            if permissions_raw:
                try:
                    permissions = json.loads(permissions_raw)
                except (json.JSONDecodeError, TypeError):
                    permissions = None
            
            results.append({
                'id':                  row[0],
                'owner_id':            row[1],
                'name':                row[2],
                'description':         row[3],
                'color':               row[4],
                'custom_instructions': row[5],
                'project_type':        row[6],
                'permissions':         permissions,
                'created_at':          row[8],
                'updated_at':          row[9],
                'is_active':           row[10],
                'conversation_count':  row[11],
                'member_count':        row[12],
                'is_owner':            bool(row[13]),
                'user_role':           row[14],
            })
        
        return results
