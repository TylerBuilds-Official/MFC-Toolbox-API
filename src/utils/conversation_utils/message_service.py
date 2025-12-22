from src.utils.conversation_utils.message import Message


class MessageService:

    @staticmethod
    def add_message(conversation_id: int, role: str, content: str,
                    model: str, provider: str, tokens_used: int = None) -> Message:

        return Message(conversation_id=conversation_id, role=role, content=content, model=model, provider=provider, tokens_used=tokens_used)