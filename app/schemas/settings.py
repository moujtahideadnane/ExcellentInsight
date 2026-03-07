"""Pydantic schemas for /settings endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# ── Profile ──────────────────────────────────────────────────────────────────


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    role: str
    is_active: bool
    org_id: uuid.UUID
    org_name: str
    org_plan: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=80)


# ── Password ──────────────────────────────────────────────────────────────────


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── API Keys ──────────────────────────────────────────────────────────────────


class ApiKeyResponse(BaseModel):
    """Shown for existing keys — full secret is NOT included."""

    id: uuid.UUID
    label: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650)


class ApiKeyCreateResponse(ApiKeyResponse):
    """Returned once at creation — includes the full plaintext key."""

    key: str  # Full secret — shown once, then discarded
