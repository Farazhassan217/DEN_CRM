from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ActionSuccessResponse(BaseModel):
    """Standardized response schema for RPC/action endpoints (e.g. /cancel, /checkin, /assign, /deactivate)."""
    success: bool = Field(True, description="Indicates whether the action succeeded")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data payload")
