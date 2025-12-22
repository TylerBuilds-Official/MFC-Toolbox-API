from src.tools.sql_tools import get_conversation
from src.tools.sql_tools.create_new_conversation import create_new_conversation
from src.tools.sql_tools.delete_conversation import delete_conversation
from src.tools.sql_tools.get_conversations_list import get_conversations_list
from src.tools.sql_tools.update_conversation import update_conversation
from src.tools.sql_tools.update_conversations_summary import update_conversation_summary
from src.utils.conversation_utils.conversation import Conversation


class ConversationService:

    @staticmethod
    def create_conversation(user_id: int, title: str = "New Conversation") -> Conversation:
        data = create_new_conversation(user_id, title)
        return Conversation(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            summary=data.get("summary"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_active=data.get("is_active")
        )




    @staticmethod
    def get_conversation(conversation_id: int, user_id: int) -> Conversation | None:
        data = get_conversation(conversation_id, user_id)

        if data is None:
            return None

        return Conversation(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            summary=data.get("summary"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_active=data.get("is_active"))




    @staticmethod
    def list_conversations(user_id: int, include_inactive=False) -> list[Conversation]:
        conversations = get_conversations_list(user_id, include_inactive=include_inactive)
        conversations_list = [
            Conversation(
                id=conversation.get("id"),
                user_id=conversation.get("user_id"),
                title=conversation.get("title"),
                summary=conversation.get("summary"),
                created_at=conversation.get("created_at"),
                updated_at=conversation.get("updated_at"),
                is_active=conversation.get("is_active")
            )
            for conversation in conversations
        ]
        return conversations_list




    @staticmethod
    def update_conversation(conversation_id: int, user_id: int, updates: dict) -> Conversation:
        updated_conversation = update_conversation(conversation_id, user_id, updates)
        if not updated_conversation:
            print(f"[ConversationService] No updates made to conversation {conversation_id}.")
            return ConversationService.get_conversation(conversation_id, user_id)

        return ConversationService.get_conversation(conversation_id, user_id)




    @staticmethod
    def update_conversation_summary(conversation_id: int, summary: str) -> None:
        return update_conversation_summary(conversation_id, summary)




    @staticmethod
    def delete_conversation(conversation_id: int, user_id: int) -> bool:
        return delete_conversation(conversation_id, user_id)
