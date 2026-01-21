# src/tools/auth/user_service.py
"""
User management service - CRUD operations against MS SQL.

Handles:
- User CRUD (create, read, update)
- Role management (base permission level)
- Specialty management (additive permission grants)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.tools.sql_tools import get_mssql_connection, SCHEMA


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
    specialty_roles: list[str] = field(default_factory=list)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_active(self) -> bool:
        """Users with 'pending' role are not yet activated."""
        return self.role in ("user", "manager", "admin")

    def has_specialty(self, specialty: str) -> bool:
        """Check if user has a specific specialty."""
        return specialty in self.specialty_roles


class UserService:
    """Handles user CRUD operations against MS SQL."""

    VALID_ROLES = {"pending", "user", "manager", "admin"}

    VALID_SPECIALTIES = {
        "drawing_coordinator",
        # Future specialties:
        # "estimator",
        # "project_manager",
        # "detailer",
    }

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @staticmethod
    def _load_specialties(user_id: int, cursor) -> list[str]:
        """Load specialty roles for a user. Internal helper."""
        cursor.execute(
            f"SELECT Specialty FROM {SCHEMA}.UserSpecialties WHERE UserId = ?",
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _build_user_from_row(row, specialties: list[str] = None) -> User:
        """Build User object from database row. Internal helper."""
        return User(
            id=row[0],
            azure_object_id=row[1],
            email=row[2],
            display_name=row[3],
            role=row[4],
            created_at=row[5],
            last_login_at=row[6],
            specialty_roles=specialties or []
        )
    
    # =========================================================================
    # User Retrieval & Creation
    # =========================================================================
    
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
                user_id = row[0]
                
                # Update last login time
                cursor.execute(
                    f"UPDATE {SCHEMA}.Users SET LastLoginAt = GETDATE() WHERE Id = ?",
                    (user_id,)
                )
                
                # Load specialties
                specialties = UserService._load_specialties(user_id, cursor)
                cursor.close()
                
                return User(
                    id=user_id,
                    azure_object_id=row[1],
                    email=row[2],
                    display_name=row[3],
                    role=row[4],
                    created_at=row[5],
                    last_login_at=datetime.now(),
                    specialty_roles=specialties
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
            
            # New users have no specialties
            return User(
                id=new_row[0],
                azure_object_id=azure_oid,
                email=email,
                display_name=display_name,
                role=new_row[1],
                created_at=new_row[2],
                last_login_at=datetime.now(),
                specialty_roles=[]
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
            
            if row:
                specialties = UserService._load_specialties(user_id, cursor)
                cursor.close()
                return UserService._build_user_from_row(row, specialties)
            
            cursor.close()
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
            
            if row:
                user_id = row[0]
                specialties = UserService._load_specialties(user_id, cursor)
                cursor.close()
                return UserService._build_user_from_row(row, specialties)
            
            cursor.close()
            return None
    
    # =========================================================================
    # Role Management
    # =========================================================================
    
    @staticmethod
    def set_user_role(user_id: int, role: str) -> bool:
        """
        Set a user's base role. Admin-only operation.
        
        Args:
            user_id: Internal user ID
            role: New role ('pending', 'user', 'manager', 'admin')
            
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
    
    # =========================================================================
    # Specialty Management
    # =========================================================================
    
    @staticmethod
    def grant_specialty(user_id: int, specialty: str, granted_by: int = None) -> bool:
        """
        Grant a specialty role to a user.
        
        Args:
            user_id: User to grant specialty to
            specialty: Specialty name (e.g., 'drawing_coordinator')
            granted_by: User ID of admin granting the specialty
            
        Returns:
            True if granted, False if user not found or already has specialty
            
        Raises:
            ValueError: If specialty is invalid
        """
        if specialty not in UserService.VALID_SPECIALTIES:
            raise ValueError(f"Invalid specialty '{specialty}'. Must be one of: {UserService.VALID_SPECIALTIES}")
        
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Check user exists
            cursor.execute(f"SELECT 1 FROM {SCHEMA}.Users WHERE Id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.close()
                return False
            
            # Try to insert (will fail silently if already exists due to unique constraint)
            try:
                cursor.execute(
                    f"INSERT INTO {SCHEMA}.UserSpecialties (UserId, Specialty, GrantedBy) "
                    f"VALUES (?, ?, ?)",
                    (user_id, specialty, granted_by)
                )
                conn.commit()
                cursor.close()
                return True
            except Exception:
                # Already has this specialty
                cursor.close()
                return False
    
    @staticmethod
    def revoke_specialty(user_id: int, specialty: str) -> bool:
        """
        Revoke a specialty role from a user.
        
        Args:
            user_id: User to revoke specialty from
            specialty: Specialty name to revoke
            
        Returns:
            True if revoked, False if user didn't have the specialty
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {SCHEMA}.UserSpecialties WHERE UserId = ? AND Specialty = ?",
                (user_id, specialty)
            )
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected > 0
    
    @staticmethod
    def get_user_specialties(user_id: int) -> list[dict]:
        """
        Get all specialties for a user with audit info.
        
        Args:
            user_id: User ID to query
            
        Returns:
            List of specialty dicts with granted_at and granted_by info
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT 
                    us.Specialty,
                    us.GrantedAt,
                    us.GrantedBy,
                    u.DisplayName as GrantedByName
                FROM {SCHEMA}.UserSpecialties us
                LEFT JOIN {SCHEMA}.Users u ON us.GrantedBy = u.Id
                WHERE us.UserId = ?
                ORDER BY us.GrantedAt DESC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            
            return [
                {
                    "specialty": row[0],
                    "granted_at": row[1].isoformat() if row[1] else None,
                    "granted_by_id": row[2],
                    "granted_by_name": row[3]
                }
                for row in rows
            ]
    
    @staticmethod
    def get_users_by_specialty(specialty: str) -> list[User]:
        """
        Get all users who have a specific specialty.
        
        Args:
            specialty: Specialty name to filter by
            
        Returns:
            List of User objects with the specified specialty
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT u.Id, u.AzureObjectId, u.Email, u.DisplayName, u.Role, u.CreatedAt, u.LastLoginAt
                FROM {SCHEMA}.Users u
                INNER JOIN {SCHEMA}.UserSpecialties us ON u.Id = us.UserId
                WHERE us.Specialty = ?
                ORDER BY u.DisplayName
                """,
                (specialty,)
            )
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                user_id = row[0]
                specialties = UserService._load_specialties(user_id, cursor)
                users.append(UserService._build_user_from_row(row, specialties))
            
            cursor.close()
            return users
    
    # =========================================================================
    # User Listing
    # =========================================================================
    
    @staticmethod
    def list_users() -> list[User]:
        """List all users with their specialties. Admin-only operation."""
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT Id, AzureObjectId, Email, DisplayName, Role, CreatedAt, LastLoginAt "
                f"FROM {SCHEMA}.Users ORDER BY CreatedAt DESC"
            )
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                user_id = row[0]
                specialties = UserService._load_specialties(user_id, cursor)
                users.append(UserService._build_user_from_row(row, specialties))
            
            cursor.close()
            return users
