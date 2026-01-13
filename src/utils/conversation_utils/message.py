from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    id: int
    conversation_id: int
    role: str
    content: str
    model: str
    provider: str
    tokens_used: int | None
    created_at: str
    user_id: int | None
    thinking: Optional[str] = None  # Extended thinking content (Claude only)
    content_blocks: Optional[str] = None  # JSON string of structured content blocks

    def to_dict(self):
        result = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at,
            "user_id": self.user_id
        }
        # Only include thinking if present (keeps response clean for non-thinking messages)
        if self.thinking:
            result["thinking"] = self.thinking
        # Only include content_blocks if present
        if self.content_blocks:
            result["content_blocks"] = self.content_blocks
        return result

    def __repr__(self):
        return (
            f"Message(id={self.id}, conversation_id={self.conversation_id}, "
            f"role='{self.role}', content='{self.content[:50]}...', "
            f"thinking={'yes' if self.thinking else 'no'}, "
            f"content_blocks={'yes' if self.content_blocks else 'no'}, "
            f"created_at='{self.created_at}', user_id={self.user_id})"
        )
