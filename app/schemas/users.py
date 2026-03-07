"""User-facing Pydantic schemas for /users endpoints.

Extracted from api/users.py so schemas live in the schemas package
alongside auth, job, dashboard, upload, etc.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Public user profile returned by GET /users/me."""

    id: uuid.UUID
    email: str
    org_id: uuid.UUID
    role: str
    is_active: bool
    display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """Body for PATCH /users/me."""

    display_name: Optional[str] = None
