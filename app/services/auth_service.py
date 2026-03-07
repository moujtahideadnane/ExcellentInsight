import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import LoginRequest, UserCreate
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

# A dummy hash to use when the user is not found, preventing timing attacks.
_DUMMY_HASH = hash_password("__dummy_passphrase_for_constant_time__")


class AuthService:
    @staticmethod
    async def signup(db: AsyncSession, user_in: UserCreate):
        # Check if user exists
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create organization
        org = Organization(name=user_in.org_name)
        db.add(org)
        await db.flush()  # Get org.id

        # Create user
        user = User(
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            org_id=org.id,
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def login(db: AsyncSession, login_in: LoginRequest):
        result = await db.execute(select(User).where(User.email == login_in.email))
        user = result.scalar_one_or_none()

        # Always run verify_password to prevent timing-based email enumeration.
        # If the user doesn't exist, we compare against a dummy hash (constant time).
        candidate_hash = user.password_hash if user else _DUMMY_HASH
        password_ok = verify_password(login_in.password, candidate_hash)

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        access_token = create_access_token(data={"sub": str(user.id), "org_id": str(user.org_id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id), "org_id": str(user.org_id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
