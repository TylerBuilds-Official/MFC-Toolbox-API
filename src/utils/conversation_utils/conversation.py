from dataclasses import dataclass

@dataclass
class Conversation:
    id: int
    user_id: int
    title: str
    summary: str
    created_at: str
    updated_at: str
    is_active: bool

    def to_dict(self):
        """Convert to API response format."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active
        }

    def __repr__(self):
        return f"Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}', summary='{self.summary}', created_at='{self.created_at}', updated_at='{self.updated_at}', is_active={self.is_active})"