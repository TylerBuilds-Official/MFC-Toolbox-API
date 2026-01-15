from fastapi import APIRouter, HTTPException, Depends
from src.tools.auth import User, require_active_user
from src.utils.conversation_utils import ConversationService, MessageService
from src.utils._dataclasses_main.create_conversation_request import CreateConversationRequest
from src.utils._dataclasses_main.update_conversation_request import UpdateConversationRequest
from src.tools.auth import get_current_user

# for reset endpoint
from src.tools.state.state_handler import StateHandler
from src.utils.conversation_state_utils import ConversationStateService

router = APIRouter()

@router.get("/conversations")
async def list_conversations(include_inactive=False, user: User = Depends(require_active_user)):
    conversations = ConversationService.list_conversations(user.id, include_inactive=include_inactive)
    #TODO add admin guard against including inactive conversations
    return {
        "conversations": [conversation.to_dict() for conversation in conversations]
    }

@router.post("/conversations")
async def create_conversation(body: CreateConversationRequest, user: User = Depends(require_active_user)):
    title = body.title if body else "New Conversation"
    conversation = ConversationService.create_conversation(user.id, title=title)
    return conversation.to_dict()


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, user: User = Depends(require_active_user)):
    """Get conversation metadata with paginated messages (most recent 50)."""
    conversation = ConversationService.get_conversation(conversation_id, user.id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get paginated messages (most recent 50)
    result = MessageService.get_messages_paginated(conversation_id, limit=50)
    messages = result["messages"]

    # Derive conversation context from messages
    # Provider from first message (conversation's original provider)
    # Model from last message (pick up where they left off)
    conversation_provider = messages[0].provider if messages else None
    conversation_model = messages[-1].model if messages else None

    return {
        "conversation": conversation.to_dict(),
        "messages": [msg.to_dict() for msg in messages],
        "conversation_provider": conversation_provider,
        "conversation_model": conversation_model,
        "has_more": result["has_more"],
        "oldest_id": result["oldest_id"],
        "total_count": result["total_count"]
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages_paginated(
    conversation_id: int,
    limit: int = 50,
    before_id: int = None,
    user: User = Depends(require_active_user)
):
    """
    Get paginated messages for a conversation.
    
    Args:
        conversation_id: The conversation to fetch messages from
        limit: Maximum messages to return (default 50, max 100)
        before_id: Cursor - only return messages with ID < this value
    
    Returns:
        messages: List of messages in chronological order
        has_more: Whether there are older messages to load
        oldest_id: Use as before_id for next page
        total_count: Total messages in conversation
    """
    # Verify ownership
    conversation = ConversationService.get_conversation(conversation_id, user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Clamp limit
    limit = min(max(1, limit), 100)
    
    result = MessageService.get_messages_paginated(
        conversation_id, 
        limit=limit, 
        before_id=before_id
    )
    
    return {
        "messages": [msg.to_dict() for msg in result["messages"]],
        "has_more": result["has_more"],
        "oldest_id": result["oldest_id"],
        "total_count": result["total_count"]
    }


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: int,
        body: UpdateConversationRequest,
        user: User = Depends(require_active_user)
):
    updates = {}
    if body.title is not None:
        updates["title"] = body.title

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    conversation = ConversationService.update_conversation(
        conversation_id,
        user.id,
        updates
    )

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation.to_dict()


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, user: User = Depends(require_active_user)):
    deleted = ConversationService.delete_conversation(conversation_id, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "status": "deleted",
        "conversation_id": conversation_id
    }


@router.post("/reset")
async def reset_conversation(conversation_id: int = None, user: User = Depends(get_current_user)):
    """
    Reset the conversation state for a specific conversation.
    If no conversation_id provided, returns an error.
    """
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    # Verify ownership
    conversation = ConversationService.get_conversation(conversation_id, user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save fresh state
    fresh_state = StateHandler(conversation_id)
    ConversationStateService.save_state(conversation_id, fresh_state.to_dict())

    return {"status": "Conversation state reset", "conversation_id": conversation_id}


