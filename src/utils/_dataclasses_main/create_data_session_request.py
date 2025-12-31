from pydantic import BaseModel
from typing import Optional


class CreateDataSessionRequest(BaseModel):
    """Request body for creating a new data session."""
    tool_name: str
    tool_params: Optional[dict] = None
    message_id: Optional[int] = None
    parent_session_id: Optional[int] = None
    visualization_config: Optional[dict] = None
