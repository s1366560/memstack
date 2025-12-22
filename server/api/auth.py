from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import create_api_key, get_current_user
from server.database import get_db
from server.db_models import APIKey as DBAPIKey
from server.db_models import User as DBUser
from server.logging_config import get_logger
from server.models.auth import APIKeyCreate, APIKeyResponse, Token
from server.models.auth import User as UserSchema

logger = get_logger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint to get an access token (API Key).
    For the demo, we check against hardcoded demo credentials.
    In a real production app, this should check password hashes.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    user = None
    # Demo credentials check
    if form_data.username == "admin@vipmemory.com" and form_data.password == "admin123":
        result = await db.execute(select(DBUser).where(DBUser.email == form_data.username))
        user = result.scalar_one_or_none()
    elif form_data.username == "user@vipmemory.com" and form_data.password == "user123":
        result = await db.execute(select(DBUser).where(DBUser.email == form_data.username))
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate a temporary session API key
    plain_key, _ = await create_api_key(
        db,
        user_id=user.id,
        name=f"Login Session {form_data.username}",
        permissions=["read", "write"] + (["admin"] if user.role == "admin" else []),
        expires_in_days=1,  # Short lived token
    )

    return {"access_token": plain_key, "token_type": "bearer"}


@router.post("/auth/keys", response_model=APIKeyResponse)
async def create_new_api_key(
    key_data: APIKeyCreate,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key."""
    plain_key, api_key = await create_api_key(
        db,
        user_id=current_user.id,
        name=key_data.name,
        permissions=key_data.permissions,
        expires_in_days=key_data.expires_in_days,
    )

    return APIKeyResponse(
        key_id=api_key.id,
        key=plain_key,  # Show only once
        name=api_key.name,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        permissions=api_key.permissions,
    )


@router.get("/auth/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: DBUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """List all API keys for the current user."""
    result = await db.execute(select(DBAPIKey).where(DBAPIKey.user_id == current_user.id))
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            key_id=k.id,
            key="*****************",  # Masked
            name=k.name,
            created_at=k.created_at,
            expires_at=k.expires_at,
            permissions=k.permissions,
        )
        for k in keys
    ]


@router.delete("/auth/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (delete) an API key."""
    result = await db.execute(
        select(DBAPIKey).where(DBAPIKey.id == key_id, DBAPIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(key)
    await db.commit()


@router.get("/users/me", response_model=UserSchema)
@router.get("/auth/me", response_model=UserSchema)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    """Get current user information."""
    logger.info(f"Reading user info for: {current_user.id}")
    return UserSchema(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        tenant_id=current_user.tenant_id,
    )
