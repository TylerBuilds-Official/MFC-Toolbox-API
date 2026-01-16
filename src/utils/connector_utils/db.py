"""
Database operations for connector configuration.
Schema: toolbox_agents
"""

from typing import Optional
from src.tools.sql_tools import get_mssql_connection
from src.utils.connector_utils.models import (
    AGENTS_SCHEMA,
    RegisteredAgent,
    ConnectorConfig,
    AllowedFolder
)


# ============================================
# Registered Agents
# ============================================

def upsert_registered_agent(
    user_id: str,
    username: str,
    hostname: str,
    agent_version: str = None
) -> RegisteredAgent:
    """
    Insert or update a registered agent.
    Updates last_seen_at on every call.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Try to update existing
        cursor.execute(f"""
            UPDATE {AGENTS_SCHEMA}.RegisteredAgents
            SET Username = ?, Hostname = ?, AgentVersion = ?, LastSeenAt = GETDATE()
            WHERE UserId = ?
        """, (username, hostname, agent_version, user_id))
        
        if cursor.rowcount == 0:
            # Insert new
            cursor.execute(f"""
                INSERT INTO {AGENTS_SCHEMA}.RegisteredAgents 
                (UserId, Username, Hostname, AgentVersion)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, hostname, agent_version))
        
        cursor.close()
    
    return get_registered_agent_by_user_id(user_id)


def get_registered_agent_by_user_id(user_id: str) -> Optional[RegisteredAgent]:
    """Get registered agent by Azure AD user ID."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, Username, Hostname, AgentVersion, 
                   FirstRegisteredAt, LastSeenAt
            FROM {AGENTS_SCHEMA}.RegisteredAgents
            WHERE UserId = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return RegisteredAgent(
                id=row[0],
                user_id=row[1],
                username=row[2],
                hostname=row[3],
                agent_version=row[4],
                first_registered_at=row[5],
                last_seen_at=row[6]
            )
        return None


def get_registered_agent_by_username(username: str) -> Optional[RegisteredAgent]:
    """Get registered agent by Windows username."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, Username, Hostname, AgentVersion, 
                   FirstRegisteredAt, LastSeenAt
            FROM {AGENTS_SCHEMA}.RegisteredAgents
            WHERE LOWER(Username) = LOWER(?)
        """, (username,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return RegisteredAgent(
                id=row[0],
                user_id=row[1],
                username=row[2],
                hostname=row[3],
                agent_version=row[4],
                first_registered_at=row[5],
                last_seen_at=row[6]
            )
        return None


def update_agent_last_seen(username: str) -> None:
    """Update last_seen_at timestamp for an agent."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {AGENTS_SCHEMA}.RegisteredAgents
            SET LastSeenAt = GETDATE()
            WHERE LOWER(Username) = LOWER(?)
        """, (username,))
        cursor.close()


# ============================================
# Connector Config
# ============================================

def get_connector_config(user_id: str, connector_type: str) -> Optional[ConnectorConfig]:
    """Get connector config for a user."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, ConnectorType, Enabled, CreatedAt, UpdatedAt
            FROM {AGENTS_SCHEMA}.UserConnectorConfig
            WHERE UserId = ? AND ConnectorType = ?
        """, (user_id, connector_type))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return ConnectorConfig(
                id=row[0],
                user_id=row[1],
                connector_type=row[2],
                enabled=bool(row[3]),
                created_at=row[4],
                updated_at=row[5]
            )
        return None


def get_or_create_connector_config(user_id: str, connector_type: str) -> ConnectorConfig:
    """Get connector config, creating with defaults if not exists."""
    config = get_connector_config(user_id, connector_type)
    
    if config is None:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {AGENTS_SCHEMA}.UserConnectorConfig 
                (UserId, ConnectorType, Enabled)
                VALUES (?, ?, 1)
            """, (user_id, connector_type))
            cursor.close()
        
        config = get_connector_config(user_id, connector_type)
    
    return config


def update_connector_enabled(user_id: str, connector_type: str, enabled: bool) -> ConnectorConfig:
    """Enable or disable a connector for a user."""
    # Ensure config exists
    get_or_create_connector_config(user_id, connector_type)
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {AGENTS_SCHEMA}.UserConnectorConfig
            SET Enabled = ?, UpdatedAt = GETDATE()
            WHERE UserId = ? AND ConnectorType = ?
        """, (1 if enabled else 0, user_id, connector_type))
        cursor.close()
    
    return get_connector_config(user_id, connector_type)


# ============================================
# Allowed Folders
# ============================================

def get_allowed_folders(user_id: str) -> list[AllowedFolder]:
    """Get all allowed folders for a user."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, Path, CanRead, CanWrite, CanDelete, CreatedAt
            FROM {AGENTS_SCHEMA}.UserAllowedFolders
            WHERE UserId = ?
            ORDER BY Path
        """, (user_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [
            AllowedFolder(
                id=row[0],
                user_id=row[1],
                path=row[2],
                can_read=bool(row[3]),
                can_write=bool(row[4]),
                can_delete=bool(row[5]),
                created_at=row[6]
            )
            for row in rows
        ]


def get_allowed_folder_by_id(folder_id: int) -> Optional[AllowedFolder]:
    """Get a specific allowed folder by ID."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, Path, CanRead, CanWrite, CanDelete, CreatedAt
            FROM {AGENTS_SCHEMA}.UserAllowedFolders
            WHERE Id = ?
        """, (folder_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return AllowedFolder(
                id=row[0],
                user_id=row[1],
                path=row[2],
                can_read=bool(row[3]),
                can_write=bool(row[4]),
                can_delete=bool(row[5]),
                created_at=row[6]
            )
        return None


def get_allowed_folder_by_path(user_id: str, path: str) -> Optional[AllowedFolder]:
    """Get a specific allowed folder by path."""
    normalized_path = path.rstrip("\\/")
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT Id, UserId, Path, CanRead, CanWrite, CanDelete, CreatedAt
            FROM {AGENTS_SCHEMA}.UserAllowedFolders
            WHERE UserId = ? AND Path = ?
        """, (user_id, normalized_path))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return AllowedFolder(
                id=row[0],
                user_id=row[1],
                path=row[2],
                can_read=bool(row[3]),
                can_write=bool(row[4]),
                can_delete=bool(row[5]),
                created_at=row[6]
            )
        return None


def add_allowed_folder(
    user_id: str,
    path: str,
    can_read: bool = True,
    can_write: bool = False,
    can_delete: bool = False
) -> AllowedFolder:
    """Add an allowed folder for a user."""
    # Normalize path (remove trailing slashes, etc.)
    normalized_path = path.rstrip("\\/")
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {AGENTS_SCHEMA}.UserAllowedFolders 
            (UserId, Path, CanRead, CanWrite, CanDelete)
            OUTPUT INSERTED.Id
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, normalized_path, 
              1 if can_read else 0,
              1 if can_write else 0,
              1 if can_delete else 0))
        
        row = cursor.fetchone()
        new_id = row[0] if row else None
        cursor.close()
    
    if new_id is None:
        # Fallback: query by unique constraint
        return get_allowed_folder_by_path(user_id, normalized_path)
    
    return get_allowed_folder_by_id(new_id)


def update_allowed_folder(
    folder_id: int,
    can_read: bool = None,
    can_write: bool = None,
    can_delete: bool = None
) -> Optional[AllowedFolder]:
    """Update permissions for an allowed folder."""
    folder = get_allowed_folder_by_id(folder_id)
    if not folder:
        return None
    
    # Build update dynamically
    updates = []
    params = []
    
    if can_read is not None:
        updates.append("CanRead = ?")
        params.append(1 if can_read else 0)
    
    if can_write is not None:
        updates.append("CanWrite = ?")
        params.append(1 if can_write else 0)
    
    if can_delete is not None:
        updates.append("CanDelete = ?")
        params.append(1 if can_delete else 0)
    
    if not updates:
        return folder
    
    params.append(folder_id)
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {AGENTS_SCHEMA}.UserAllowedFolders
            SET {', '.join(updates)}
            WHERE Id = ?
        """, params)
        cursor.close()
    
    return get_allowed_folder_by_id(folder_id)


def delete_allowed_folder(folder_id: int, user_id: str) -> bool:
    """Delete an allowed folder. Returns True if deleted."""
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        # Only delete if owned by user
        cursor.execute(f"""
            DELETE FROM {AGENTS_SCHEMA}.UserAllowedFolders
            WHERE Id = ? AND UserId = ?
        """, (folder_id, user_id))
        
        deleted = cursor.rowcount > 0
        cursor.close()
        
    return deleted


# ============================================
# Permission Checking
# ============================================

def check_path_permission(user_id: str, path: str, action: str = "read") -> bool:
    """
    Check if a user has permission for a path.
    
    Args:
        user_id: The user's ID
        path: The path to check
        action: "read", "write", or "delete"
        
    Returns:
        True if permission granted, False otherwise
    """
    # First check if connector is enabled
    config = get_connector_config(user_id, "filesystem")
    if not config or not config.enabled:
        return False
    
    # Get all allowed folders
    folders = get_allowed_folders(user_id)
    
    # Normalize the path for comparison
    normalized_path = path.replace("/", "\\").rstrip("\\").lower()
    
    for folder in folders:
        normalized_folder = folder.path.replace("/", "\\").rstrip("\\").lower()
        
        # Check if path is under this folder
        if normalized_path == normalized_folder or normalized_path.startswith(normalized_folder + "\\"):
            # Path is under this folder, check specific permission
            if action == "read" and folder.can_read:
                return True
            elif action == "write" and folder.can_write:
                return True
            elif action == "delete" and folder.can_delete:
                return True
    
    return False
