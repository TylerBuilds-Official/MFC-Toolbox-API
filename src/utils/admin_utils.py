"""
Admin utilities for dashboard stats, user activity, and cross-user queries.
"""
from datetime import datetime, timedelta
from typing import Optional
from src.tools.sql_tools import get_mssql_connection, SCHEMA


class AdminStatsService:
    """Aggregated statistics for admin dashboard."""

    @staticmethod
    def get_dashboard_stats() -> dict:
        """
        Get comprehensive dashboard statistics.
        
        Returns:
            Dict with user, conversation, message, memory, and data session stats
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate date boundaries
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)
            
            # ===== USER STATS =====
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN Role = 'admin' THEN 1 ELSE 0 END) as admin_count,
                    SUM(CASE WHEN Role = 'manager' THEN 1 ELSE 0 END) as manager_count,
                    SUM(CASE WHEN Role = 'user' THEN 1 ELSE 0 END) as user_count,
                    SUM(CASE WHEN Role = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN LastLoginAt >= ? THEN 1 ELSE 0 END) as active_today,
                    SUM(CASE WHEN LastLoginAt >= ? THEN 1 ELSE 0 END) as active_this_week
                FROM {SCHEMA}.Users
            """, (today, week_ago))
            user_row = cursor.fetchone()
            
            user_stats = {
                "total": user_row[0] or 0,
                "by_role": {
                    "admin": user_row[1] or 0,
                    "manager": user_row[2] or 0,
                    "user": user_row[3] or 0,
                    "pending": user_row[4] or 0,
                },
                "active_today": user_row[5] or 0,
                "active_this_week": user_row[6] or 0,
            }
            
            # ===== CONVERSATION STATS =====
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN IsActive = 1 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN CreatedAt >= ? THEN 1 ELSE 0 END) as this_week
                FROM {SCHEMA}.Conversations
            """, (week_ago,))
            conv_row = cursor.fetchone()
            
            conversation_stats = {
                "total": conv_row[0] or 0,
                "active": conv_row[1] or 0,
                "this_week": conv_row[2] or 0,
            }
            
            # ===== MESSAGE STATS =====
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN CreatedAt >= ? THEN 1 ELSE 0 END) as this_week
                FROM {SCHEMA}.Messages
            """, (week_ago,))
            msg_row = cursor.fetchone()
            
            message_stats = {
                "total": msg_row[0] or 0,
                "this_week": msg_row[1] or 0,
            }
            
            # ===== MEMORY STATS =====
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN MemoryType = 'fact' THEN 1 ELSE 0 END) as fact_count,
                    SUM(CASE WHEN MemoryType = 'preference' THEN 1 ELSE 0 END) as preference_count,
                    SUM(CASE WHEN MemoryType = 'project' THEN 1 ELSE 0 END) as project_count,
                    SUM(CASE WHEN MemoryType = 'skill' THEN 1 ELSE 0 END) as skill_count,
                    SUM(CASE WHEN MemoryType = 'context' THEN 1 ELSE 0 END) as context_count
                FROM {SCHEMA}.UserMemories
                WHERE IsActive = 1
            """)
            mem_row = cursor.fetchone()
            
            memory_stats = {
                "total": mem_row[0] or 0,
                "by_type": {
                    "fact": mem_row[1] or 0,
                    "preference": mem_row[2] or 0,
                    "project": mem_row[3] or 0,
                    "skill": mem_row[4] or 0,
                    "context": mem_row[5] or 0,
                },
            }
            
            # ===== DATA SESSION STATS =====
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN Status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN Status = 'error' THEN 1 ELSE 0 END) as error_count,
                    SUM(CASE WHEN Status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN Status = 'running' THEN 1 ELSE 0 END) as running_count
                FROM {SCHEMA}.DataSessions
                WHERE IsActive = 1
            """)
            ds_row = cursor.fetchone()
            
            data_session_stats = {
                "total": ds_row[0] or 0,
                "by_status": {
                    "success": ds_row[1] or 0,
                    "error": ds_row[2] or 0,
                    "pending": ds_row[3] or 0,
                    "running": ds_row[4] or 0,
                },
            }
            
            cursor.close()
            
            return {
                "users": user_stats,
                "conversations": conversation_stats,
                "messages": message_stats,
                "memories": memory_stats,
                "data_sessions": data_session_stats,
                "generated_at": datetime.now().isoformat(),
            }


class AdminUserActivityService:
    """User activity details for admin view."""

    @staticmethod
    def get_user_activity(user_id: int) -> Optional[dict]:
        """
        Get detailed activity stats for a specific user.
        
        Args:
            user_id: The user's internal ID
            
        Returns:
            Dict with activity details or None if user not found
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Get user basics
            cursor.execute(f"""
                SELECT Id, Email, DisplayName, Role, CreatedAt, LastLoginAt
                FROM {SCHEMA}.Users
                WHERE Id = ?
            """, (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                cursor.close()
                return None
            
            # Get conversation stats
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as conversation_count,
                    MAX(UpdatedAt) as last_conversation_at
                FROM {SCHEMA}.Conversations
                WHERE UserId = ? AND IsActive = 1
            """, (user_id,))
            conv_row = cursor.fetchone()
            
            # Get message count
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {SCHEMA}.Messages m
                INNER JOIN {SCHEMA}.Conversations c ON m.ConversationId = c.Id
                WHERE c.UserId = ?
            """, (user_id,))
            message_count = cursor.fetchone()[0] or 0
            
            # Get memory count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {SCHEMA}.UserMemories
                WHERE UserId = ? AND IsActive = 1
            """, (user_id,))
            memory_count = cursor.fetchone()[0] or 0
            
            # Get data session count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {SCHEMA}.DataSessions
                WHERE UserId = ? AND IsActive = 1
            """, (user_id,))
            data_session_count = cursor.fetchone()[0] or 0
            
            # Get recent conversations (last 10)
            cursor.execute(f"""
                SELECT TOP 10
                    c.Id,
                    c.Title,
                    c.UpdatedAt,
                    (SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = c.Id) as message_count
                FROM {SCHEMA}.Conversations c
                WHERE c.UserId = ? AND c.IsActive = 1
                ORDER BY c.UpdatedAt DESC
            """, (user_id,))
            recent_rows = cursor.fetchall()
            
            recent_conversations = [
                {
                    "id": row[0],
                    "title": row[1],
                    "updated_at": row[2].isoformat() if row[2] else None,
                    "message_count": row[3] or 0,
                }
                for row in recent_rows
            ]
            
            cursor.close()
            
            return {
                "user_id": user_row[0],
                "email": user_row[1],
                "display_name": user_row[2],
                "role": user_row[3],
                "created_at": user_row[4].isoformat() if user_row[4] else None,
                "last_login_at": user_row[5].isoformat() if user_row[5] else None,
                "conversation_count": conv_row[0] or 0,
                "message_count": message_count,
                "memory_count": memory_count,
                "data_session_count": data_session_count,
                "last_conversation_at": conv_row[1].isoformat() if conv_row[1] else None,
                "recent_conversations": recent_conversations,
            }


class AdminConversationService:
    """Cross-user conversation queries for admin."""

    @staticmethod
    def list_all_conversations(
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
        include_inactive: bool = False,
    ) -> dict:
        """
        List conversations across all users (admin view).
        
        Args:
            limit: Max results (default 50)
            offset: Pagination offset
            user_id: Filter by specific user (optional)
            include_inactive: Include soft-deleted conversations
            
        Returns:
            Dict with conversations list and total count
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause
            conditions = []
            params = []
            
            if not include_inactive:
                conditions.append("c.IsActive = 1")
            
            if user_id is not None:
                conditions.append("c.UserId = ?")
                params.append(user_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {SCHEMA}.Conversations c
                {where_clause}
            """, params)
            total = cursor.fetchone()[0] or 0
            
            # Get conversations with user info
            cursor.execute(f"""
                SELECT 
                    c.Id,
                    c.UserId,
                    u.DisplayName as UserName,
                    u.Email as UserEmail,
                    c.Title,
                    c.Summary,
                    c.IsActive,
                    c.CreatedAt,
                    c.UpdatedAt,
                    (SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = c.Id) as MessageCount
                FROM {SCHEMA}.Conversations c
                INNER JOIN {SCHEMA}.Users u ON c.UserId = u.Id
                {where_clause}
                ORDER BY c.UpdatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, limit])
            
            rows = cursor.fetchall()
            cursor.close()
            
            conversations = [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "user_email": row[3],
                    "title": row[4],
                    "summary": row[5],
                    "is_active": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "message_count": row[9] or 0,
                }
                for row in rows
            ]
            
            return {
                "conversations": conversations,
                "total": total,
                "limit": limit,
                "offset": offset,
            }


class AdminMemoryService:
    """Cross-user memory queries for admin."""

    @staticmethod
    def list_all_memories(
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
        memory_type: Optional[str] = None,
        include_inactive: bool = False,
    ) -> dict:
        """
        List memories across all users (admin view).
        
        Args:
            limit: Max results (default 50)
            offset: Pagination offset
            user_id: Filter by specific user (optional)
            memory_type: Filter by memory type (optional)
            include_inactive: Include soft-deleted memories
            
        Returns:
            Dict with memories list and total count
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause
            conditions = []
            params = []
            
            if not include_inactive:
                conditions.append("m.IsActive = 1")
            
            if user_id is not None:
                conditions.append("m.UserId = ?")
                params.append(user_id)
            
            if memory_type is not None:
                conditions.append("m.MemoryType = ?")
                params.append(memory_type)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {SCHEMA}.UserMemories m
                {where_clause}
            """, params)
            total = cursor.fetchone()[0] or 0
            
            # Get memories with user info
            cursor.execute(f"""
                SELECT 
                    m.Id,
                    m.UserId,
                    u.DisplayName as UserName,
                    u.Email as UserEmail,
                    m.Content,
                    m.MemoryType,
                    m.ReferenceCount,
                    m.IsActive,
                    m.CreatedAt,
                    m.UpdatedAt,
                    m.LastReferencedAt
                FROM {SCHEMA}.UserMemories m
                INNER JOIN {SCHEMA}.Users u ON m.UserId = u.Id
                {where_clause}
                ORDER BY m.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, limit])
            
            rows = cursor.fetchall()
            cursor.close()
            
            memories = [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "user_email": row[3],
                    "content": row[4],
                    "memory_type": row[5],
                    "reference_count": row[6] or 0,
                    "is_active": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "updated_at": row[9].isoformat() if row[9] else None,
                    "last_referenced_at": row[10].isoformat() if row[10] else None,
                }
                for row in rows
            ]
            
            return {
                "memories": memories,
                "total": total,
                "limit": limit,
                "offset": offset,
            }


# =============================================================================
# P2: Tool Usage Stats
# =============================================================================

class AdminToolStatsService:
    """Tool usage statistics from DataSessions."""

    @staticmethod
    def get_tool_stats() -> dict:
        """
        Get usage statistics for all tools.
        
        Returns:
            Dict with tool usage metrics including execution counts,
            success rates, and recent activity.
        """
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Get aggregated stats per tool
            cursor.execute(f"""
                SELECT 
                    ToolName,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN Status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN Status = 'error' THEN 1 ELSE 0 END) as error_count,
                    SUM(CASE WHEN Status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN Status = 'running' THEN 1 ELSE 0 END) as running_count,
                    MAX(CreatedAt) as last_used,
                    COUNT(DISTINCT UserId) as unique_users
                FROM {SCHEMA}.DataSessions
                WHERE IsActive = 1
                GROUP BY ToolName
                ORDER BY total_executions DESC
            """)
            rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                total = row[1] or 0
                success = row[2] or 0
                success_rate = round(success / total, 3) if total > 0 else 0.0
                
                tools.append({
                    "name": row[0],
                    "total_executions": total,
                    "success_count": success,
                    "error_count": row[3] or 0,
                    "pending_count": row[4] or 0,
                    "running_count": row[5] or 0,
                    "success_rate": success_rate,
                    "last_used": row[6].isoformat() if row[6] else None,
                    "unique_users": row[7] or 0,
                })
            
            # Get weekly trend (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute(f"""
                SELECT 
                    CAST(CreatedAt AS DATE) as day,
                    COUNT(*) as executions
                FROM {SCHEMA}.DataSessions
                WHERE IsActive = 1 AND CreatedAt >= ?
                GROUP BY CAST(CreatedAt AS DATE)
                ORDER BY day ASC
            """, (week_ago,))
            trend_rows = cursor.fetchall()
            
            daily_trend = [
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "executions": row[1] or 0,
                }
                for row in trend_rows
            ]
            
            cursor.close()
            
            return {
                "tools": tools,
                "tool_count": len(tools),
                "daily_trend": daily_trend,
                "generated_at": datetime.now().isoformat(),
            }


# =============================================================================
# P2: Audit Log
# =============================================================================

class AdminAuditService:
    """
    Admin audit log service.
    
    Note: This currently logs to an in-memory list and the database.
    For a production system, you'd want a dedicated AuditLog table.
    """
    
    # In-memory audit log (temporary until dedicated table exists)
    _audit_log: list[dict] = []
    _max_entries = 1000  # Keep last 1000 entries in memory
    
    @classmethod
    def log_action(
        cls,
        action: str,
        actor_id: int,
        actor_name: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> dict:
        """
        Log an admin action.
        
        Args:
            action: Action type (e.g., 'role_change', 'specialty_grant')
            actor_id: User ID of admin performing action
            actor_name: Display name of admin
            target_type: Type of target ('user', 'conversation', etc.)
            target_id: ID of target entity
            target_name: Display name of target
            details: Additional details dict
            
        Returns:
            The created audit entry
        """
        entry = {
            "id": len(cls._audit_log) + 1,
            "action": action,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "target_type": target_type,
            "target_id": target_id,
            "target_name": target_name,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        cls._audit_log.append(entry)
        
        # Trim if over max
        if len(cls._audit_log) > cls._max_entries:
            cls._audit_log = cls._audit_log[-cls._max_entries:]
        
        return entry
    
    @classmethod
    def get_audit_log(
        cls,
        limit: int = 50,
        offset: int = 0,
        action_type: Optional[str] = None,
        actor_id: Optional[int] = None,
        target_type: Optional[str] = None,
    ) -> dict:
        """
        Get audit log entries with optional filtering.
        
        Args:
            limit: Max results (default 50)
            offset: Pagination offset
            action_type: Filter by action type
            actor_id: Filter by actor (admin) ID
            target_type: Filter by target type
            
        Returns:
            Dict with events list and total count
        """
        # Filter entries
        filtered = cls._audit_log.copy()
        
        if action_type:
            filtered = [e for e in filtered if e["action"] == action_type]
        
        if actor_id:
            filtered = [e for e in filtered if e["actor_id"] == actor_id]
        
        if target_type:
            filtered = [e for e in filtered if e["target_type"] == target_type]
        
        # Sort by timestamp descending (most recent first)
        filtered.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Paginate
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return {
            "events": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    @classmethod
    def get_action_types(cls) -> list[str]:
        """Get list of all action types that have been logged."""
        return list(set(e["action"] for e in cls._audit_log))


# =============================================================================
# P3: Extended Health Check
# =============================================================================

class AdminHealthService:
    """Extended health check for admin dashboard."""
    
    # Track server start time
    _start_time: datetime = datetime.now()

    @classmethod
    def get_health_status(cls) -> dict:
        """
        Get extended health status including database and agent info.
        
        Returns:
            Dict with health metrics
        """
        import time
        
        health = {
            "status": "healthy",
            "version": "0.3.0",
            "uptime_seconds": int((datetime.now() - cls._start_time).total_seconds()),
            "checks": {},
        }
        
        # Database check
        db_status = cls._check_database()
        health["checks"]["database"] = db_status
        if not db_status["connected"]:
            health["status"] = "degraded"
        
        # Agent connections check
        agent_status = cls._check_agents()
        health["checks"]["agents"] = agent_status
        
        health["generated_at"] = datetime.now().isoformat()
        
        return health
    
    @staticmethod
    def _check_database() -> dict:
        """Check database connectivity and measure latency."""
        import time
        
        try:
            start = time.time()
            with get_mssql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            latency_ms = round((time.time() - start) * 1000, 2)
            
            return {
                "connected": True,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }
    
    @staticmethod
    def _check_agents() -> dict:
        """Check connected agents status."""
        try:
            from src.utils.agent_utils import agent_registry
            
            agents = agent_registry.list_agents()
            return {
                "connected_count": len(agents),
                "agents": [
                    {
                        "username": a.get("username"),
                        "hostname": a.get("hostname"),
                        "connected_at": a.get("connected_at"),
                    }
                    for a in agents
                ],
            }
        except Exception as e:
            return {
                "connected_count": 0,
                "error": str(e),
            }
