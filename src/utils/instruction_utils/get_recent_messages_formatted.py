from src.tools.sql_tools.messages.get_recent_messages import get_recent_exchanges


def get_recent_exchanges_formatted(conversation_id: int, limit: int = 6) -> str:
    """Format recent exchanges for injection into system prompt."""
    exchanges = get_recent_exchanges(conversation_id, limit)
    
    if not exchanges:
        return ""
    
    formatted = []
    for msg in exchanges:
        prefix = "[User]" if msg['role'] == 'user' else "[Assistant]"
        formatted.append(f"{prefix}: {msg['content']}")
    
    return "\n".join(formatted)