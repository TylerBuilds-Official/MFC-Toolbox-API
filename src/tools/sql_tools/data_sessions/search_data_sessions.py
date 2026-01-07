"""
Search data sessions by keyword with weighted relevance scoring.
Uses stored procedure: Toolbox_SearchDataSessions
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def search_data_sessions(
    user_id: int,
    query: str,
    limit: int = 20
) -> dict:
    """
    Search data sessions by keyword across title, summary, tool_name, and tool_params.
    Returns ranked results with relevance scores and match indicators.
    
    Args:
        user_id: The user's ID
        query: Search keywords
        limit: Maximum results (default 20, max 50)
        
    Returns:
        Dict with query info and ranked session results
    """
    limit = min(max(limit, 1), 50)
    query = query.strip()
    
    if not query:
        return {"query": query, "result_count": 0, "results": []}
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_SearchDataSessions @UserId=?, @Query=?, @Limit=?",
            (user_id, query, limit)
        )
        
        rows = cursor.fetchall()
        cursor.close()
        
        results = []
        for row in rows:
            # Build matched_in list from match flags
            matched_in = []
            if row[17]:  # TitleMatch
                matched_in.append("title")
            if row[18]:  # SummaryMatch
                matched_in.append("summary")
            if row[19]:  # ToolNameMatch
                matched_in.append("tool_name")
            if row[20]:  # ToolParamsMatch
                matched_in.append("tool_params")
            
            # Extract match snippets
            match_snippets = []
            if row[17] and row[12]:  # TitleMatch and Title exists
                snippet = _extract_snippet(row[12], query, context_chars=75)
                if snippet:
                    match_snippets.append({"source": "title", "text": snippet})
            if row[18] and row[13]:  # SummaryMatch and Summary exists
                snippet = _extract_snippet(row[13], query, context_chars=150)
                if snippet:
                    match_snippets.append({"source": "summary", "text": snippet})
            
            results.append({
                "session_id": row[0],
                "user_id": row[1],
                "message_id": row[2],
                "session_group_id": row[3],
                "parent_session_id": row[4],
                "tool_name": row[5],
                "tool_params": json.loads(row[6]) if row[6] else None,
                "status": row[8],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
                "title": row[12],
                "summary": row[13],
                "has_results": bool(row[14]),
                "row_count": row[15],
                "columns": json.loads(row[16]) if row[16] else None,
                "matched_in": matched_in,
                "match_snippets": match_snippets,
                "relevance_score": round(float(row[21]), 3),  # RelevanceScore
            })
        
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
