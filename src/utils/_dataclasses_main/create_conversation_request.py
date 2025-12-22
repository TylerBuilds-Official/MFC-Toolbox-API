from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass

@dataclass
class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"