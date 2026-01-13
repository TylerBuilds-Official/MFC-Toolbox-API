from src.tools.sql_tools import (get_messages, add_message, get_message, 
                                 update_message_artifact, link_artifacts_to_message)
from src.utils.conversation_utils.message import Message


class MessageService:

    @staticmethod
    def add_message(conversation_id: int, role: str,
                    content: str, model: str,
                    provider: str, tokens_used: int = None,
                    user_id: int = None, thinking: str = None,
                    content_blocks: str = None) -> Message:

        data = add_message(
            conversation_id=conversation_id, 
            role=role,
            content=content, 
            model=model,
            provider=provider, 
            tokens_used=tokens_used, 
            user_id=user_id,
            thinking=thinking,
            content_blocks=content_blocks
        )

        return Message(
            id=data.get("id"),
            conversation_id=data.get("conversation_id"),
            role=data.get("role"),
            content=data.get("content"),
            model=data.get("model"),
            provider=data.get("provider"),
            tokens_used=data.get("tokens_used"),
            created_at=data.get("created_at"),
            user_id=data.get("user_id"),
            thinking=data.get("thinking"),
            content_blocks=data.get("content_blocks")
        )


    @staticmethod
    def get_message(message_id: int) -> Message | None:
        data = get_message(message_id)
        if data is None:
            return None
        return Message(
            id=data.get("id"),
            conversation_id=data.get("conversation_id"),
            role=data.get("role"),
            content=data.get("content"),
            model=data.get("model"),
            provider=data.get("provider"),
            tokens_used=data.get("tokens_used"),
            created_at=data.get("created_at"),
            user_id=data.get("user_id"),
            thinking=data.get("thinking"),
            content_blocks=data.get("content_blocks")
        )


    @staticmethod
    def get_messages(conversation_id: int, limit: int = None) -> list[Message]:
        messages_data = get_messages(conversation_id, limit=limit)
        return [
            Message(
                id=message.get("id"),
                conversation_id=message.get("conversation_id"),
                role=message.get("role"),
                content=message.get("content"),
                model=message.get("model"),
                provider=message.get("provider"),
                tokens_used=message.get("tokens_used"),
                created_at=message.get("created_at"),
                user_id=message.get("user_id"),
                thinking=message.get("thinking"),
                content_blocks=message.get("content_blocks")
            )
        for message in messages_data]

    @staticmethod
    def link_artifacts(conversation_id: int, message_id: int) -> list[str]:
        """
        Links any orphaned artifacts in the conversation to the specified message.
        Also updates the message with the first artifact_id found.
        
        Args:
            conversation_id: The conversation to search for orphaned artifacts
            message_id: The message ID to link artifacts to
            
        Returns:
            List of artifact IDs that were linked
        """
        # Link orphaned artifacts to this message
        artifact_ids = link_artifacts_to_message(conversation_id, message_id)
        
        # If any artifacts were linked, update the message with the first one
        if artifact_ids:
            update_message_artifact(message_id, artifact_ids[0])
        
        return artifact_ids
