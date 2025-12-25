"""
Authentication middleware and dependencies for API Key validation.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from server.database import async_session_factory, get_db
from server.db_models import APIKey as DBAPIKey
from server.db_models import Permission, Role, RolePermission, Tenant, UserRole, UserTenant
from server.db_models import User as DBUser
from server.logging_config import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


def generate_api_key() -> str:
    """Generate a new API key."""
    random_bytes = secrets.token_bytes(32)
    key = f"ms_sk_{random_bytes.hex()}"
    return key


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(key) == hashed_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.debug(f"verify_password failed with error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


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

    if not api_key.startswith("ms_sk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. API keys should start with 'ms_sk_'",
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
    result = await db.execute(
        select(DBUser)
        .where(DBUser.id == api_key.user_id)
        .options(selectinload(DBUser.roles).selectinload(UserRole.role))
    )
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


async def create_user(db: AsyncSession, email: str, name: str, password: str) -> DBUser:
    """Create a new user."""
    # Check if user exists
    result = await db.execute(select(DBUser).where(DBUser.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return existing_user

    hashed = get_password_hash(password)
    logger.debug(f"create_user hashed password to '{hashed}'")
    user = DBUser(
        id=str(uuid4()),
        email=email,
        name=name,
        password_hash=hashed,
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
            # 1. Initialize Permissions
            permissions_data = [
                {
                    "code": "tenant:create",
                    "name": "Create Tenant",
                    "description": "Create new tenants",
                },
                {
                    "code": "tenant:read",
                    "name": "Read Tenant",
                    "description": "View tenant details",
                },
                {
                    "code": "tenant:update",
                    "name": "Update Tenant",
                    "description": "Update tenant details",
                },
                {"code": "tenant:delete", "name": "Delete Tenant", "description": "Delete tenants"},
                {
                    "code": "project:create",
                    "name": "Create Project",
                    "description": "Create new projects",
                },
                {
                    "code": "project:read",
                    "name": "Read Project",
                    "description": "View project details",
                },
                {
                    "code": "project:update",
                    "name": "Update Project",
                    "description": "Update project details",
                },
                {
                    "code": "project:delete",
                    "name": "Delete Project",
                    "description": "Delete projects",
                },
                {
                    "code": "memory:create",
                    "name": "Create Memory",
                    "description": "Create new memories",
                },
                {"code": "memory:read", "name": "Read Memory", "description": "View memories"},
                {"code": "user:read", "name": "Read User", "description": "View user details"},
                {
                    "code": "user:update",
                    "name": "Update User",
                    "description": "Update user details",
                },
            ]

            created_permissions = {}
            for perm_data in permissions_data:
                result = await db.execute(
                    select(Permission).where(Permission.code == perm_data["code"])
                )
                perm = result.scalar_one_or_none()
                if not perm:
                    perm = Permission(id=str(uuid4()), **perm_data)
                    db.add(perm)
                    await db.commit()
                    await db.refresh(perm)
                created_permissions[perm_data["code"]] = perm

            # 2. Initialize Roles
            roles_data = [
                {"name": "admin", "description": "System Administrator"},
                {"name": "user", "description": "Regular User"},
            ]

            created_roles = {}
            for role_data in roles_data:
                result = await db.execute(select(Role).where(Role.name == role_data["name"]))
                role = result.scalar_one_or_none()
                if not role:
                    role = Role(id=str(uuid4()), **role_data)
                    db.add(role)
                    await db.commit()
                    await db.refresh(role)
                created_roles[role_data["name"]] = role

            # 3. Assign Permissions to Roles
            # Admin gets all permissions
            admin_role = created_roles["admin"]
            for perm in created_permissions.values():
                result = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == admin_role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(
                        RolePermission(
                            id=str(uuid4()), role_id=admin_role.id, permission_id=perm.id
                        )
                    )

            # User gets read permissions
            user_role = created_roles["user"]
            for code, perm in created_permissions.items():
                if "read" in code or "create" in code:
                    result = await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == user_role.id,
                            RolePermission.permission_id == perm.id,
                        )
                    )
                    if not result.scalar_one_or_none():
                        db.add(
                            RolePermission(
                                id=str(uuid4()), role_id=user_role.id, permission_id=perm.id
                            )
                        )

            await db.commit()

            # 4. Create Users
            # Check if default user exists
            result = await db.execute(select(DBUser).where(DBUser.email == "admin@memstack.ai"))
            user = result.scalar_one_or_none()

            # Check if default tenant exists
            result = await db.execute(select(Tenant).where(Tenant.name == "Default Tenant"))
            default_tenant = result.scalar_one_or_none()

            if not user:
                user = await create_user(
                    db, email="admin@memstack.ai", name="Default Admin", password="adminpassword"
                )

                # Assign Admin Role
                db.add(UserRole(id=str(uuid4()), user_id=user.id, role_id=admin_role.id))

                plain_key, _ = await create_api_key(
                    db,
                    user_id=user.id,
                    name="Default API Key",
                    permissions=["read", "write", "admin"],
                )

                logger.info(f"🔑 Default Admin API Key created: {plain_key}")
                logger.info(f"👤 Default Admin ID: {user.id}")
                logger.info(f"📧 Default Admin Email: {user.email}")
                logger.info("🔑 Default Admin Password: adminpassword")

                # Create Default Tenant if not exists and assign admin as owner
                if not default_tenant:
                    default_tenant = Tenant(
                        id=str(uuid4()),
                        name="Default Tenant",
                        description="Default tenant for demonstration",
                        owner_id=user.id,
                        plan="enterprise",
                        max_projects=10,
                        max_users=100,
                        max_storage=10737418240,  # 10GB
                    )
                    db.add(default_tenant)
                    await db.flush()  # flush to get ID
                    logger.info(f"🏢 Default Tenant created: {default_tenant.id}")

                    # Add admin as owner of the tenant
                    admin_tenant_membership = UserTenant(
                        id=str(uuid4()),
                        user_id=user.id,
                        tenant_id=default_tenant.id,
                        role="owner",
                        permissions={"admin": True},
                    )
                    db.add(admin_tenant_membership)

            # If user exists but tenant was just created (edge case or partial init), ensure membership
            elif default_tenant:
                # Check if admin is member
                result = await db.execute(
                    select(UserTenant).where(
                        UserTenant.user_id == user.id, UserTenant.tenant_id == default_tenant.id
                    )
                )
                if not result.scalar_one_or_none():
                    admin_tenant_membership = UserTenant(
                        id=str(uuid4()),
                        user_id=user.id,
                        tenant_id=default_tenant.id,
                        role="owner",
                        permissions={"admin": True},
                    )
                    db.add(admin_tenant_membership)

            # Check if default regular user exists
            result = await db.execute(select(DBUser).where(DBUser.email == "user@memstack.ai"))
            normal_user = result.scalar_one_or_none()

            if not normal_user:
                normal_user = await create_user(
                    db, email="user@memstack.ai", name="Default User", password="userpassword"
                )

                # Assign User Role
                db.add(UserRole(id=str(uuid4()), user_id=normal_user.id, role_id=user_role.id))

                plain_user_key, _ = await create_api_key(
                    db,
                    user_id=normal_user.id,
                    name="Default User Key",
                    permissions=["read", "write"],
                )

                logger.info(f"🔑 Default User API Key created: {plain_user_key}")
                logger.info(f"👤 Default User ID: {normal_user.id}")
                logger.info(f"📧 Default User Email: {normal_user.email}")
                logger.info("🔑 Default User Password: userpassword")

                # Add normal user to default tenant as member
                if default_tenant:
                    user_tenant_membership = UserTenant(
                        id=str(uuid4()),
                        user_id=normal_user.id,
                        tenant_id=default_tenant.id,
                        role="member",
                        permissions={"read": True, "write": True},
                    )
                    db.add(user_tenant_membership)

            elif default_tenant and normal_user:
                # Check if normal user is member
                result = await db.execute(
                    select(UserTenant).where(
                        UserTenant.user_id == normal_user.id,
                        UserTenant.tenant_id == default_tenant.id,
                    )
                )
                if not result.scalar_one_or_none():
                    user_tenant_membership = UserTenant(
                        id=str(uuid4()),
                        user_id=normal_user.id,
                        tenant_id=default_tenant.id,
                        role="member",
                        permissions={"read": True, "write": True},
                    )
                    db.add(user_tenant_membership)

            await db.commit()

        except Exception as e:
            logger.exception(f"Error initializing default credentials: {e}")
