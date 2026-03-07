import uuid
from typing import Optional

from pydantic import BaseModel, Field


class RetryRequest(BaseModel):
    """Request to retry a failed or interrupted job from a specific step."""

    from_step: str = Field(..., description="The step name to restart from (e.g. 'llm', 'stats')")
    params: Optional[dict] = Field(None, description="Optional parameter overrides for the retry attempt")


class RetryResponse(BaseModel):
    """Response after successfully enqueuing a retry attempt."""

    job_id: uuid.UUID
    status: str
    message: str
