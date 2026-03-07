"""Settings API — profile, password, and API-key management.

Endpoints:
  GET  /settings/profile                → Full profile + org info
  PATCH /settings/profile               → Update display name
  POST /settings/change-password        → Change password (requires current)
  GET  /settings/api-keys               → List all personal API keys
  POST /settings/api-keys               → Create a new API key (returns secret once)
  DELETE /settings/api-keys/{key_id}    → Revoke / delete an API key
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_org_id, get_current_user_id, get_rls_db
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.user import User
from app.schemas.errors import (
    RESPONSES_400,
    RESPONSES_401,
    RESPONSES_403,
    RESPONSES_404,
)
from app.schemas.settings import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    ChangePasswordRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.utils.security import hash_password, verify_password

logger = structlog.get_logger()

router = APIRouter(prefix="/settings", tags=["Settings"])

_KEY_PREFIX = "ei_"
_MAX_KEYS_PER_USER = 20


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_user_and_org(
    db: AsyncSession,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
) -> tuple[User, Organization]:
    """Load user + org in one round-trip; raise 404 if missing."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return user, org


def _hash_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key for safe storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, prefix, hash)."""
    token = secrets.token_urlsafe(32)
    full_key = f"{_KEY_PREFIX}{token}"
    prefix = full_key[:12]  # "ei_" + first 9 chars
    return full_key, prefix, _hash_key(full_key)


# ── Profile ───────────────────────────────────────────────────────────────────


@router.get(
    "/profile",
    response_model=ProfileResponse,
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def get_profile(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Return full profile including org details."""
    user, org = await _get_user_and_org(db, current_user_id, current_org_id)
    return ProfileResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        org_id=org.id,
        org_name=org.name,
        org_plan=org.plan,
        created_at=user.created_at,
    )


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_404},
)
async def update_profile(
    body: ProfileUpdateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Update mutable profile fields (currently: display_name)."""
    user, org = await _get_user_and_org(db, current_user_id, current_org_id)

    if body.display_name is not None:
        user.display_name = body.display_name.strip() or None

    await db.commit()
    await db.refresh(user)

    return ProfileResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        org_id=org.id,
        org_name=org.name,
        org_plan=org.plan,
        created_at=user.created_at,
    )


# ── Password ──────────────────────────────────────────────────────────────────


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_403},
)
async def change_password(
    body: ChangePasswordRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Change the current user's password after verifying the existing one."""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current password is incorrect",
        )

    if body.new_password == body.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from the current password",
        )

    user.password_hash = hash_password(body.new_password)
    await db.commit()
    logger.info("password_changed", user_id=str(current_user_id))


# ── API Keys ──────────────────────────────────────────────────────────────────


@router.get(
    "/api-keys",
    response_model=List[ApiKeyResponse],
    responses={**RESPONSES_401},
)
async def list_api_keys(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """List all API keys belonging to the current user."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user_id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return keys


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**RESPONSES_400, **RESPONSES_401},
)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Create a new personal API key.  The full key is returned only once."""
    # Enforce per-user cap
    count_result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == current_user_id,
            ApiKey.is_active == True,  # noqa: E712
        )
    )
    if len(count_result.scalars().all()) >= _MAX_KEYS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {_MAX_KEYS_PER_USER} active API keys reached",
        )

    full_key, prefix, key_hash = _generate_api_key()

    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    api_key = ApiKey(
        user_id=current_user_id,
        org_id=current_org_id,
        label=body.label.strip(),
        key_prefix=prefix,
        key_hash=key_hash,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("api_key_created", user_id=str(current_user_id), key_prefix=prefix)

    return ApiKeyCreateResponse(
        id=api_key.id,
        label=api_key.label,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        key=full_key,  # Shown once
    )


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Permanently revoke (delete) an API key owned by the current user."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user_id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found",
        )

    await db.delete(key)
    await db.commit()
    logger.info("api_key_revoked", key_id=str(key_id), user_id=str(current_user_id))
