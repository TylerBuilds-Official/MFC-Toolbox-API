from pydantic import BaseModel
from typing import Optional


class UpdateDataSessionRequest(BaseModel):
    """Request body for updating a data session."""
    visualization_config: Optional[dict] = None
    status: Optional[str] = None
