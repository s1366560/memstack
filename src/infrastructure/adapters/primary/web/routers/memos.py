"""Memos API routes for personal notes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.secondary.persistence.database import get_db
from src.infrastructure.adapters.secondary.persistence.models import User
from src.configuration.di_container import DIContainer
from src.application.use_cases.memo import (
    CreateMemoCommand,
    GetMemoQuery,
    ListMemosQuery,
    UpdateMemoCommand,
    DeleteMemoCommand,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["memos"])


# --- Schemas ---

class MemoCreate(BaseModel):
    content: str
    visibility: str = "PRIVATE"  # PRIVATE, PUBLIC, PROTECTED
    tags: List[str] = []


class MemoUpdate(BaseModel):
    content: str = None
    visibility: str = None
    tags: List[str] = None


class MemoResponse(BaseModel):
    id: str
    content: str
    visibility: str
    tags: List[str]
    created_at: str
    updated_at: str = None


# --- Helper Functions ---

def memo_to_response(memo) -> MemoResponse:
    """Convert domain Memo to response DTO"""
    return MemoResponse(
        id=memo.id,
        content=memo.content,
        visibility=memo.visibility,
        tags=memo.tags,
        created_at=memo.created_at.isoformat(),
        updated_at=memo.updated_at.isoformat() if memo.updated_at else None
    )


# --- FastAPI Dependencies for Use Cases ---

async def get_di_container(db: AsyncSession = Depends(get_db)) -> DIContainer:
    """Get DI container with use cases"""
    return DIContainer(db)


# --- Endpoints ---

@router.post("/memos", response_model=MemoResponse, status_code=status.HTTP_201_CREATED)
async def create_memo(
    memo_data: MemoCreate,
    current_user: User = Depends(get_current_user),
    container: DIContainer = Depends(get_di_container),
):
    """Create a new memo."""
    try:
        # Get use case from DI container
        use_case = container.create_memo_use_case()

        # Execute use case
        command = CreateMemoCommand(
            content=memo_data.content,
            user_id=current_user.id,
            visibility=memo_data.visibility,
            tags=memo_data.tags,
        )
        memo = await use_case.execute(command)

        return memo_to_response(memo)

    except Exception as e:
        logger.error(f"Failed to create memo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memos", response_model=List[MemoResponse])
async def list_memos(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    container: DIContainer = Depends(get_di_container),
):
    """List memos for the current user."""
    try:
        # Get use case from DI container
        use_case = container.list_memos_use_case()

        # Execute use case
        query = ListMemosQuery(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        memos = await use_case.execute(query)

        return [memo_to_response(m) for m in memos]

    except Exception as e:
        logger.error(f"Failed to list memos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memos/{memo_id}", response_model=MemoResponse)
async def get_memo(
    memo_id: str,
    current_user: User = Depends(get_current_user),
    container: DIContainer = Depends(get_di_container),
):
    """Get a memo by ID."""
    try:
        # Get use case from DI container
        use_case = container.get_memo_use_case()

        # Execute use case
        query = GetMemoQuery(
            memo_id=memo_id,
            user_id=current_user.id,
        )
        memo = await use_case.execute(query)

        if not memo:
            raise HTTPException(status_code=404, detail="Memo not found")

        return memo_to_response(memo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/memos/{memo_id}", response_model=MemoResponse)
async def update_memo(
    memo_id: str,
    memo_data: MemoUpdate,
    current_user: User = Depends(get_current_user),
    container: DIContainer = Depends(get_di_container),
):
    """Update a memo."""
    try:
        # Get use case from DI container
        use_case = container.update_memo_use_case()

        # Execute use case
        command = UpdateMemoCommand(
            memo_id=memo_id,
            user_id=current_user.id,
            content=memo_data.content,
            visibility=memo_data.visibility,
            tags=memo_data.tags,
        )
        memo = await use_case.execute(command)

        if not memo:
            raise HTTPException(status_code=404, detail="Memo not found")

        return memo_to_response(memo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memo(
    memo_id: str,
    current_user: User = Depends(get_current_user),
    container: DIContainer = Depends(get_di_container),
):
    """Delete a memo."""
    try:
        # Get use case from DI container
        use_case = container.delete_memo_use_case()

        # Execute use case
        command = DeleteMemoCommand(
            memo_id=memo_id,
            user_id=current_user.id,
        )
        deleted = await use_case.execute(command)

        if not deleted:
            raise HTTPException(status_code=404, detail="Memo not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
