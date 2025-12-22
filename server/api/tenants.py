"""Tenant management API endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import get_current_user
from server.database import get_db
from server.db_models import Tenant, User, UserTenant
from server.models import TenantCreate, TenantListResponse, TenantResponse, TenantUpdate

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Create a new tenant."""
    # Check if user already owns a tenant
    result = await db.execute(select(Tenant).where(Tenant.owner_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already owns a tenant"
        )

    # Create tenant
    tenant_id = str(uuid4())
    tenant = Tenant(
        id=tenant_id,
        name=tenant_data.name,
        description=tenant_data.description,
        owner_id=current_user.id,
        plan=tenant_data.plan,
        max_projects=tenant_data.max_projects,
        max_users=tenant_data.max_users,
        max_storage=tenant_data.max_storage,
    )
    db.add(tenant)
    await db.flush()

    # Create user-tenant relationship
    user_tenant = UserTenant(
        id=str(uuid4()),
        user_id=current_user.id,
        tenant_id=tenant.id,
        role="owner",
        permissions={"admin": True, "create_projects": True, "manage_users": True},
    )
    db.add(user_tenant)
    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.from_orm(tenant)


@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantListResponse:
    """List tenants for the current user."""
    # Get tenant IDs user has access to
    user_tenants_result = await db.execute(
        select(UserTenant.tenant_id).where(UserTenant.user_id == current_user.id)
    )
    tenant_ids = [row[0] for row in user_tenants_result.fetchall()]

    if not tenant_ids:
        return TenantListResponse(tenants=[], total=0, page=page, page_size=page_size)

    # Build query
    query = select(Tenant).where(Tenant.id.in_(tenant_ids))

    if search:
        query = query.where(
            or_(
                Tenant.name.ilike(f"%{search}%"),
                Tenant.description.ilike(f"%{search}%"),
            )
        )

    # Get total count
    count_query = select(func.count(Tenant.id)).where(Tenant.id.in_(tenant_ids))
    if search:
        count_query = count_query.where(
            or_(
                Tenant.name.ilike(f"%{search}%"),
                Tenant.description.ilike(f"%{search}%"),
            )
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tenants = result.scalars().all()

    return TenantListResponse(
        tenants=[TenantResponse.from_orm(tenant) for tenant in tenants],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Get tenant by ID."""
    # Check if user has access to tenant
    user_tenant_result = await db.execute(
        select(UserTenant).where(
            and_(UserTenant.user_id == current_user.id, UserTenant.tenant_id == tenant_id)
        )
    )
    if not user_tenant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to tenant"
        )

    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantResponse.from_orm(tenant)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Update tenant."""
    # Check if user is owner
    result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can update tenant"
        )

    # Update fields
    update_data = tenant_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.from_orm(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete tenant."""
    # Check if user is owner
    result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can delete tenant"
        )

    await db.delete(tenant)
    await db.commit()


@router.post("/{tenant_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_tenant_member(
    tenant_id: str,
    user_id: str,
    role: str = Query("member", description="Member role"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add member to tenant."""
    # Check if current user is owner
    result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can add members"
        )

    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is already member
    existing_result = await db.execute(
        select(UserTenant).where(
            and_(UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id)
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this tenant"
        )

    # Create user-tenant relationship
    user_tenant = UserTenant(
        id=str(uuid4()),
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        permissions={"read": True, "write": role in ["admin", "member"]},
    )
    db.add(user_tenant)
    await db.commit()

    return {"message": "Member added successfully", "user_id": user_id, "role": role}


@router.delete("/{tenant_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tenant_member(
    tenant_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove member from tenant."""
    # Check if current user is owner
    result = await db.execute(
        select(Tenant).where(
            and_(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can remove members"
        )

    # Cannot remove owner
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove tenant owner"
        )

    # Remove user-tenant relationship
    result = await db.execute(
        select(UserTenant).where(
            and_(UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id)
        )
    )
    user_tenant = result.scalar_one_or_none()
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this tenant"
        )

    await db.delete(user_tenant)
    await db.commit()


@router.get("/{tenant_id}/members")
async def list_tenant_members(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List tenant members."""
    # Check if user has access to tenant
    user_tenant_result = await db.execute(
        select(UserTenant).where(
            and_(UserTenant.user_id == current_user.id, UserTenant.tenant_id == tenant_id)
        )
    )
    if not user_tenant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to tenant"
        )

    # Get all members
    result = await db.execute(
        select(UserTenant, User)
        .join(User, UserTenant.user_id == User.id)
        .where(UserTenant.tenant_id == tenant_id)
    )
    members = []
    for user_tenant, user in result.fetchall():
        members.append({
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user_tenant.role,
            "permissions": user_tenant.permissions,
            "created_at": user_tenant.created_at,
        })

    return {"members": members, "total": len(members)}