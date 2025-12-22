from dataclasses import dataclass

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

    def to_dict(self):
        return {
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

    def __repr__(self):
        return f"Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}', content='{self.content}', created_at='{self.created_at}, user_id={self.user_id}')"