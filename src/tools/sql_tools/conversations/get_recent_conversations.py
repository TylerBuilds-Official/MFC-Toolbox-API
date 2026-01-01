from datetime import datetime, timedelta
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_recent_conversations(
    user_id: int, 
    days_back: int = 7, 
    limit: int = 10
) -> list[dict]:
    """
    Get recent conversations within a time window.
    
    Args:
        user_id: The user's ID
        days_back: How many days to look back (default 7, max 90)
        limit: Maximum results to return (default 10, max 20)
        
    Returns:
        List of conversation dicts with metadata, sorted by most recent activity
    """
    # Enforce limits
    days_back = min(max(days_back, 1), 90)
    limit = min(max(limit, 1), 20)
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            SELECT 
                c.Id,
                c.Title,
                c.Summary,
                c.CreatedAt,
                c.UpdatedAt,
                c.LastMessagePreview,
                (SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = c.Id) as MessageCount
            FROM {SCHEMA}.Conversations c
            WHERE c.UserId = ? 
              AND c.IsActive = 1
              AND c.UpdatedAt >= ?
            ORDER BY c.UpdatedAt DESC
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """,
            (user_id, cutoff_date, limit)
        )
        
        columns = ['id', 'title', 'summary', 'created_at', 'updated_at', 'last_message_preview', 'message_count']
        rows = cursor.fetchall()
        cursor.close()
        
        results = []
        for row in rows:
            results.append({
                "conversation_id": row[0],
                "title": row[1],
                "summary": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "last_activity": row[4].isoformat() if row[4] else None,
                "last_message_preview": row[5],
                "message_count": row[6],
            })
        
        return results
