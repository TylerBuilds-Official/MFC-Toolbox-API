from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass

@dataclass
class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None