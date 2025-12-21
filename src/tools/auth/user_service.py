# src/tools/auth/user_service.py
"""
User management service - CRUD operations against MS SQL.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


@dataclass
class User:
    """Represents an authenticated user."""
    id: int
    azure_object_id: str
    email: str
    display_name: str
    role: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    @property
    def is_active(self) -> bool:
        """Users with 'pending' role are not yet activated."""
        return self.role in ("user", "admin")


class UserService:
    """Handles user CRUD operations against MS SQL."""
    
    VALID_ROLES = {"pending", "user", "admin"}
    
    @staticmethod
    def get_or_create_user(azure_oid: str, email: str, display_name: str) -> User:
        """
        Find user by Azure Object ID, or create if first sign-in.
        Updates last_login_at on each call.
        
        Args:
            azure_oid: Azure AD object ID from token
            email: User's email from token
            display_name: User's display name from token
            
        Returns:
            User object (existing or newly created)
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Try to find existing user
            cursor.execute(
                f"SELECT Id, AzureObjectId, Email, DisplayName, Role, CreatedAt, LastLoginAt "
                f"FROM {SCHEMA}.Users WHERE AzureObjectId = ?",
                (azure_oid,))

            row = cursor.fetchone()
            
            if row:
                # Update last login time
                cursor.execute(
                    f"UPDATE {SCHEMA}.Users SET LastLoginAt = GETDATE() WHERE Id = ?",
                    (row[0],)
                )
                cursor.close()
                return User(
                    id=row[0],
                    azure_object_id=row[1],
                    email=row[2],
                    display_name=row[3],
                    role=row[4],
                    created_at=row[5],
                    last_login_at=datetime.now()
                )
            
            # Create new user (trigger will auto-create UserSettings)
            cursor.execute(
                f"INSERT INTO {SCHEMA}.Users (AzureObjectId, Email, DisplayName, LastLoginAt) "
                f"VALUES (?, ?, ?, GETDATE())",
                (azure_oid, email, display_name)
            )
            conn.commit()
            
            cursor.execute(
                f"SELECT Id, Role, CreatedAt FROM {SCHEMA}.Users WHERE AzureObjectId = ?",
                (azure_oid,)
            )
            new_row = cursor.fetchone()
            cursor.close()
            
            if not new_row:
                raise Exception("Failed to create user")
            
            return User(
                id=new_row[0],
                azure_object_id=azure_oid,
                email=email,
                display_name=display_name,
                role=new_row[1],
                created_at=new_row[2],
                last_login_at=datetime.now()
            )
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Fetch a user by their internal ID."""
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT Id, AzureObjectId, Email, DisplayName, Role, CreatedAt, LastLoginAt "
                f"FROM {SCHEMA}.Users WHERE Id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return User(
                    id=row[0],
                    azure_object_id=row[1],
                    email=row[2],
                    display_name=row[3],
                    role=row[4],
                    created_at=row[5],
                    last_login_at=row[6]
                )
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Fetch a user by their email address."""
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT Id, AzureObjectId, Email, DisplayName, Role, CreatedAt, LastLoginAt "
                f"FROM {SCHEMA}.Users WHERE Email = ?",
                (email,)
            )
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return User(
                    id=row[0],
                    azure_object_id=row[1],
                    email=row[2],
                    display_name=row[3],
                    role=row[4],
                    created_at=row[5],
                    last_login_at=row[6]
                )
            return None
    
    @staticmethod
    def set_user_role(user_id: int, role: str) -> bool:
        """
        Set a user's role. Admin-only operation.
        
        Args:
            user_id: Internal user ID
            role: New role ('pending', 'user', 'admin')
            
        Returns:
            True if update succeeded, False if user not found
            
        Raises:
            ValueError: If role is invalid
        """
        if role not in UserService.VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {UserService.VALID_ROLES}")
        
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {SCHEMA}.Users SET Role = ? WHERE Id = ?",
                (role, user_id)
            )
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
    
    @staticmethod
    def list_users() -> list[User]:
        """List all users. Admin-only operation."""
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT Id, AzureObjectId, Email, DisplayName, Role, CreatedAt, LastLoginAt "
                f"FROM {SCHEMA}.Users ORDER BY CreatedAt DESC"
            )
            rows = cursor.fetchall()
            cursor.close()
            
            return [
                User(
                    id=row[0],
                    azure_object_id=row[1],
                    email=row[2],
                    display_name=row[3],
                    role=row[4],
                    created_at=row[5],
                    last_login_at=row[6]
                )
                for row in rows
            ]
