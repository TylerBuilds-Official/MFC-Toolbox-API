import re
from datetime import datetime, timedelta
from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def search_conversations(
    user_id: int,
    query: str,
    limit: int = 10
) -> dict:
    """
    Search conversations by keyword across titles, summaries, and messages.
    Returns ranked results with context snippets.
    
    Args:
        user_id: The user's ID
        query: Search keywords
        limit: Maximum results (default 10, max 20)
        
    Returns:
        Dict with query info and ranked results
    """
    limit = min(max(limit, 1), 20)
    query = query.strip()
    
    if not query:
        return {"query": query, "result_count": 0, "results": []}
    
    search_pattern = f"%{query}%"
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Step 1: Find conversations with title/summary matches
        cursor.execute(
            f"""
            SELECT 
                c.Id,
                c.Title,
                c.Summary,
                c.CreatedAt,
                c.UpdatedAt,
                c.LastMessagePreview,
                CASE WHEN c.Title LIKE ? THEN 1 ELSE 0 END as TitleMatch,
                CASE WHEN c.Summary LIKE ? THEN 1 ELSE 0 END as SummaryMatch,
                (SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = c.Id) as MessageCount
            FROM {SCHEMA}.Conversations c
            WHERE c.UserId = ? 
              AND c.IsActive = 1
              AND (c.Title LIKE ? OR c.Summary LIKE ?)
            """,
            (search_pattern, search_pattern, user_id, search_pattern, search_pattern)
        )
        
        conv_matches = {}
        for row in cursor.fetchall():
            conv_id = row[0]
            conv_matches[conv_id] = {
                "conversation_id": conv_id,
                "title": row[1],
                "summary": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "last_message_preview": row[5],
                "title_match": bool(row[6]),
                "summary_match": bool(row[7]),
                "message_match": False,
                "message_count": row[8],
                "match_snippets": [],
            }
            
            # Extract snippet from title if matched
            if row[6] and row[1]:
                snippet = _extract_snippet(row[1], query, context_chars=75)
                if snippet:
                    conv_matches[conv_id]["match_snippets"].append({
                        "source": "title",
                        "text": snippet
                    })
            
            # Extract snippet from summary if matched
            if row[7] and row[2]:
                snippet = _extract_snippet(row[2], query, context_chars=150)
                if snippet:
                    conv_matches[conv_id]["match_snippets"].append({
                        "source": "summary",
                        "text": snippet
                    })
        
        # Step 2: Find conversations with message matches
        # Get user's conversation IDs first
        cursor.execute(
            f"""
            SELECT Id FROM {SCHEMA}.Conversations 
            WHERE UserId = ? AND IsActive = 1
            """,
            (user_id,)
        )
        user_conv_ids = [row[0] for row in cursor.fetchall()]
        
        if user_conv_ids:
            # Find messages with matches
            placeholders = ','.join('?' * len(user_conv_ids))
            cursor.execute(
                f"""
                SELECT 
                    m.ConversationId,
                    m.Content,
                    m.CreatedAt,
                    c.Title,
                    c.Summary,
                    c.CreatedAt as ConvCreatedAt,
                    c.UpdatedAt,
                    c.LastMessagePreview,
                    (SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = c.Id) as MessageCount
                FROM {SCHEMA}.Messages m
                JOIN {SCHEMA}.Conversations c ON m.ConversationId = c.Id
                WHERE m.ConversationId IN ({placeholders})
                  AND m.Content LIKE ?
                  AND m.Role IN ('user', 'assistant')
                ORDER BY m.CreatedAt DESC
                """,
                (*user_conv_ids, search_pattern)
            )
            
            for row in cursor.fetchall():
                conv_id = row[0]
                
                if conv_id not in conv_matches:
                    # New conversation found via message match
                    conv_matches[conv_id] = {
                        "conversation_id": conv_id,
                        "title": row[3],
                        "summary": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                        "last_message_preview": row[7],
                        "title_match": False,
                        "summary_match": False,
                        "message_match": True,
                        "message_count": row[8],
                        "match_snippets": [],
                    }
                else:
                    conv_matches[conv_id]["message_match"] = True
                
                # Add message snippet (limit to 2 per conversation)
                existing_msg_snippets = sum(
                    1 for s in conv_matches[conv_id]["match_snippets"] 
                    if s["source"] == "message"
                )
                if existing_msg_snippets < 2 and row[1]:
                    snippet = _extract_snippet(row[1], query, context_chars=150)
                    if snippet:
                        conv_matches[conv_id]["match_snippets"].append({
                            "source": "message",
                            "text": snippet
                        })
        
        cursor.close()
    
    # Step 3: Compute relevance scores and rank
    now = datetime.now()
    results = []
    
    for conv_id, data in conv_matches.items():
        # Compute relevance score
        score = 0.0
        
        # Title match: 0.4 weight
        if data["title_match"]:
            score += 0.4
        
        # Summary match: 0.3 weight
        if data["summary_match"]:
            score += 0.3
        
        # Message match: 0.2 weight
        if data["message_match"]:
            score += 0.2
        
        # Recency: 0.1 weight (decay over 30 days)
        if data["updated_at"]:
            days_old = (now - data["updated_at"]).days
            recency_score = max(0, 1 - (days_old / 30)) * 0.1
            score += recency_score
        
        # Build matched_in list
        matched_in = []
        if data["title_match"]:
            matched_in.append("title")
        if data["summary_match"]:
            matched_in.append("summary")
        if data["message_match"]:
            matched_in.append("messages")
        
        # Format result
        results.append({
            "conversation_id": data["conversation_id"],
            "title": data["title"],
            "summary": data["summary"],
            "match_snippets": data["match_snippets"],
            "matched_in": matched_in,
            "message_count": data["message_count"],
            "created_at": data["created_at"].isoformat() if data["created_at"] else None,
            "last_activity": data["updated_at"].isoformat() if data["updated_at"] else None,
            "relevance_score": round(score, 3),
        })
    
    # Sort by relevance score descending
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Apply limit
    results = results[:limit]
    
    return {
        "query": query,
        "result_count": len(results),
        "results": results,
    }


def _extract_snippet(text: str, query: str, context_chars: int = 150) -> str | None:
    """
    Extract a snippet from text around the query match with ||highlighting||.
    
    Args:
        text: The text to search
        query: The search term
        context_chars: Characters of context on each side
        
    Returns:
        Snippet with highlighted match, or None if no match
    """
    if not text or not query:
        return None
    
    # Case-insensitive search
    text_lower = text.lower()
    query_lower = query.lower()
    
    match_pos = text_lower.find(query_lower)
    if match_pos == -1:
        return None
    
    # Calculate snippet bounds
    start = max(0, match_pos - context_chars)
    end = min(len(text), match_pos + len(query) + context_chars)
    
    # Extract snippet
    snippet = text[start:end]
    
    # Find the match position in the snippet and add highlights
    snippet_match_pos = match_pos - start
    highlighted = (
        snippet[:snippet_match_pos] +
        "||" +
        snippet[snippet_match_pos:snippet_match_pos + len(query)] +
        "||" +
        snippet[snippet_match_pos + len(query):]
    )
    
    # Add ellipsis if truncated
    if start > 0:
        highlighted = "..." + highlighted
    if end < len(text):
        highlighted = highlighted + "..."
    
    return highlighted
