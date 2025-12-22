"""
Authentication middleware and dependencies for API Key validation.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import async_session_factory, get_db
from server.db_models import APIKey as DBAPIKey
from server.db_models import User as DBUser

security = HTTPBearer()


def generate_api_key() -> str:
    """Generate a new API key."""
    random_bytes = secrets.token_bytes(32)
    key = f"vpm_sk_{random_bytes.hex()}"
    return key


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(key) == hashed_key


async def get_api_key_from_header(
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract API key from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide an API key in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    elif authorization.startswith("Token "):
        api_key = authorization[6:]
    else:
        api_key = authorization

    if not api_key.startswith("vpm_sk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. API keys should start with 'vpm_sk_'",
        )

    return api_key


async def verify_api_key_dependency(
    api_key: str = Depends(get_api_key_from_header), db: AsyncSession = Depends(get_db)
) -> DBAPIKey:
    """
    Dependency to verify API key from request header.
    """
    hashed_key = hash_api_key(api_key)

    # Query DB for key
    result = await db.execute(select(DBAPIKey).where(DBAPIKey.key_hash == hashed_key))
    stored_key = result.scalar_one_or_none()

    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not stored_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been deactivated",
        )

    if stored_key.expires_at and stored_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last used timestamp
    stored_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(stored_key)

    return stored_key


async def get_current_user(
    api_key: DBAPIKey = Depends(verify_api_key_dependency), db: AsyncSession = Depends(get_db)
) -> DBUser:
    """
    Get the current user from the API key.
    """
    result = await db.execute(select(DBUser).where(DBUser.id == api_key.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def create_api_key(
    db: AsyncSession,
    user_id: str,
    name: str,
    permissions: list[str],
    expires_in_days: Optional[int] = None,
) -> Tuple[str, DBAPIKey]:
    """
    Create a new API key for a user.
    Returns (plain_key, stored_key) tuple.
    """
    plain_key = generate_api_key()
    hashed_key = hash_api_key(plain_key)

    expires_at = None
    if expires_in_days:
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    api_key = DBAPIKey(
        id=str(uuid4()),
        key_hash=hashed_key,
        name=name,
        user_id=user_id,
        permissions=permissions,
        expires_at=expires_at,
        is_active=True,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return plain_key, api_key


async def create_user(
    db: AsyncSession, email: str, name: str, role: str = "user", tenant_id: Optional[str] = None
) -> DBUser:
    """Create a new user."""
    # Check if user exists
    result = await db.execute(select(DBUser).where(DBUser.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return existing_user

    user = DBUser(
        id=str(uuid4()),
        email=email,
        name=name,
        role=role,
        tenant_id=tenant_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def initialize_default_credentials():
    """Initialize default user and API key for development."""
    async with async_session_factory() as db:
        try:
            # Check if default user exists
            result = await db.execute(select(DBUser).where(DBUser.email == "admin@vipmemory.com"))
            user = result.scalar_one_or_none()

            if not user:
                user = await create_user(
                    db,
                    email="admin@vipmemory.com",
                    name="Default Admin",
                    role="admin",
                )

                plain_key, _ = await create_api_key(
                    db,
                    user_id=user.id,
                    name="Default API Key",
                    permissions=["read", "write", "admin"],
                )

                print(f"🔑 Default Admin API Key created: {plain_key}")
                print(f"👤 Default Admin ID: {user.id}")
                print(f"📧 Default Admin Email: {user.email}")

            # Check if default regular user exists
            result = await db.execute(select(DBUser).where(DBUser.email == "user@vipmemory.com"))
            normal_user = result.scalar_one_or_none()

            if not normal_user:
                normal_user = await create_user(
                    db,
                    email="user@vipmemory.com",
                    name="Default User",
                    role="user",
                )

                print(f"👤 Default User ID: {normal_user.id}")
                print(f"📧 Default User Email: {normal_user.email}")

        except Exception as e:
            print(f"Error initializing default credentials: {e}")
