import uuid
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.storage.local_storage import LocalStorageBackend
from app.utils.security import decode_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{settings.API_VERSION}/auth/login", auto_error=False)


def get_storage():
    return LocalStorageBackend(base_path=settings.STORAGE_LOCAL_PATH)


async def get_token(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
    query_token: Optional[str] = Query(None, alias="token"),
) -> str:
    token = header_token or query_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Enforce Redis-backed blocklist used by /auth/logout.
    # SECURITY: In production we fail-closed — a Redis outage means we cannot
    # verify token revocation, so we reject the request with 503 to avoid
    # allowing revoked tokens. In development we fail-open for convenience.
    try:
        redis_conn = getattr(request.app.state, "redis", None)
        _managed = False
        if redis_conn is None:
            redis_conn = redis.from_url(settings.REDIS_URL, decode_responses=False)
            _managed = True

        is_blocked = await redis_conn.get(f"blocklist:{token}")
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
    except HTTPException:
        raise
    except Exception:
        if settings.APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable. Please retry.",
            ) from None
        # In development/staging: fail-open so Redis outages don't block local work.
    finally:
        if "redis_conn" in locals() and _managed and redis_conn is not None:
            try:
                await redis_conn.aclose()
            except Exception:
                pass

    return token


async def get_current_user_id(token: str = Depends(get_token)) -> uuid.UUID:
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from None


async def get_current_org_id(token: str = Depends(get_token)) -> uuid.UUID:
    try:
        payload = decode_token(token)
        org_id = payload.get("org_id")
        if org_id is None or str(org_id) == "00000000-0000-0000-0000-000000000000":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return uuid.UUID(org_id)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from None


async def get_rls_db(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AsyncSession:
    """Dependency that returns a DB session with RLS context pre-set."""
    from app.db.session import set_db_context

    await set_db_context(db, str(org_id), str(user_id))
    return db
