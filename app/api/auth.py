import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_token
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserCreate
from app.schemas.errors import RESPONSES_400, RESPONSES_401, RESPONSES_403
from app.services.auth_service import AuthService
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**RESPONSES_400},
)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    await AuthService.signup(db, user_in)
    # Login immediately after signup
    return await AuthService.login(db, LoginRequest(email=user_in.email, password=user_in.password))


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={**RESPONSES_401, **RESPONSES_403},
)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(db, login_in)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={**RESPONSES_401},
)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_refresh_token(body.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = await AuthService.get_user_by_id(db, uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        new_access_token = create_access_token(data={"sub": str(user.id), "org_id": str(user.org_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id), "org_id": str(user.org_id)})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=user,
        )
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, token: str = Depends(get_token)):
    """
    Adds the current access token to a Redis blocklist for the remainder of its TTL
    so it cannot be reused after explicit logout.
    """
    import time

    import structlog

    from app.config import get_settings
    from app.utils.security import decode_token

    settings = get_settings()
    logger = structlog.get_logger()

    try:
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        ttl = max(int(exp - time.time()), 1)

        # Always use the shared Redis pool from app.state
        r = getattr(request.app.state, "redis", None)

        if r is None:
            # Redis unavailable - log warning but allow logout to succeed
            logger.warning(
                "logout_redis_unavailable",
                msg="Cannot blocklist token due to Redis unavailability. Token will remain valid until expiry."
            )
            # Logout should always succeed from the client's perspective
            return

        await r.setex(f"blocklist:{token}", ttl, "1")
        logger.debug("token_blocklisted", ttl=ttl)

    except Exception as e:
        # Logout should always succeed from the client's perspective
        # but log the error for monitoring
        logger.error("logout_blocklist_failed", error=str(e))
