from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import get_current_user
from server.database import get_db
from server.db_models import Memo as DBMemo
from server.db_models import User as DBUser
from server.models.memos import MemoCreate, MemoResponse, MemoUpdate

router = APIRouter(tags=["Memos"])


@router.post("/memos", response_model=MemoResponse)
async def create_memo(
    memo_data: MemoCreate,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new memo."""
    memo = DBMemo(
        id=str(uuid4()),
        content=memo_data.content,
        visibility=memo_data.visibility,
        tags=memo_data.tags,
        user_id=current_user.id,
    )
    db.add(memo)
    await db.commit()
    await db.refresh(memo)
    return memo


@router.get("/memos", response_model=List[MemoResponse])
async def list_memos(
    limit: int = 20,
    offset: int = 0,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List memos."""
    stmt = (
        select(DBMemo)
        .where(DBMemo.user_id == current_user.id)
        .order_by(desc(DBMemo.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/memos/{memo_id}", response_model=MemoResponse)
async def get_memo(
    memo_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a memo by ID."""
    result = await db.execute(
        select(DBMemo).where(DBMemo.id == memo_id, DBMemo.user_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")
    return memo


@router.patch("/memos/{memo_id}", response_model=MemoResponse)
async def update_memo(
    memo_id: str,
    memo_data: MemoUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a memo."""
    result = await db.execute(
        select(DBMemo).where(DBMemo.id == memo_id, DBMemo.user_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    if memo_data.content is not None:
        memo.content = memo_data.content
    if memo_data.visibility is not None:
        memo.visibility = memo_data.visibility
    if memo_data.tags is not None:
        memo.tags = memo_data.tags

    await db.commit()
    await db.refresh(memo)
    return memo


@router.delete("/memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memo(
    memo_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a memo."""
    result = await db.execute(
        select(DBMemo).where(DBMemo.id == memo_id, DBMemo.user_id == current_user.id)
    )
    memo = result.scalar_one_or_none()
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    await db.delete(memo)
    await db.commit()
