"""
SQLAlchemy implementation of MemoRepository.
"""

import logging
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository
from src.infrastructure.adapters.secondary.persistence.models import Memo as DBMemo

logger = logging.getLogger(__name__)


class SqlAlchemyMemoRepository(MemoRepository):
    """SQLAlchemy implementation of MemoRepository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, memo: Memo) -> None:
        """Save a memo (create or update)"""
        result = await self._session.execute(
            select(DBMemo).where(DBMemo.id == memo.id)
        )
        db_memo = result.scalar_one_or_none()

        if db_memo:
            # Update existing memo
            db_memo.content = memo.content
            db_memo.visibility = memo.visibility
            db_memo.tags = memo.tags
            db_memo.updated_at = memo.updated_at
        else:
            # Create new memo
            db_memo = DBMemo(
                id=memo.id,
                content=memo.content,
                user_id=memo.user_id,
                visibility=memo.visibility,
                tags=memo.tags,
                created_at=memo.created_at,
                updated_at=memo.updated_at,
            )
            self._session.add(db_memo)

        await self._session.flush()

    async def find_by_id(self, memo_id: str) -> Optional[Memo]:
        """Find a memo by ID"""
        result = await self._session.execute(
            select(DBMemo).where(DBMemo.id == memo_id)
        )
        db_memo = result.scalar_one_or_none()
        return self._to_domain(db_memo) if db_memo else None

    async def find_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memo]:
        """List all memos for a user"""
        result = await self._session.execute(
            select(DBMemo)
            .where(DBMemo.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        db_memos = result.scalars().all()
        return [self._to_domain(m) for m in db_memos]

    async def list_by_visibility(
        self,
        user_id: str,
        visibility: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memo]:
        """List memos by visibility level"""
        result = await self._session.execute(
            select(DBMemo)
            .where(DBMemo.user_id == user_id)
            .where(DBMemo.visibility == visibility)
            .offset(offset)
            .limit(limit)
        )
        db_memos = result.scalars().all()
        return [self._to_domain(m) for m in db_memos]

    async def delete(self, memo_id: str) -> None:
        """Delete a memo"""
        result = await self._session.execute(
            select(DBMemo).where(DBMemo.id == memo_id)
        )
        db_memo = result.scalar_one_or_none()
        if db_memo:
            await self._session.delete(db_memo)
            await self._session.flush()

    def _to_domain(self, db_memo: DBMemo) -> Memo:
        """Convert database model to domain model"""
        return Memo(
            id=db_memo.id,
            content=db_memo.content,
            user_id=db_memo.user_id,
            visibility=db_memo.visibility,
            tags=db_memo.tags,
            created_at=db_memo.created_at,
            updated_at=db_memo.updated_at,
        )
