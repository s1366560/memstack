from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from src.domain.model.memo.memo import Memo


class MemoRepository(ABC):
    """Repository interface for Memo entity"""

    @abstractmethod
    async def save(self, memo: Memo) -> None:
        """Save a memo (create or update)"""
        pass

    @abstractmethod
    async def find_by_id(self, memo_id: str) -> Optional[Memo]:
        """Find a memo by ID"""
        pass

    @abstractmethod
    async def find_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Memo]:
        """List all memos for a user"""
        pass

    @abstractmethod
    async def list_by_visibility(
        self,
        user_id: str,
        visibility: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memo]:
        """List memos by visibility level"""
        pass

    @abstractmethod
    async def delete(self, memo_id: str) -> None:
        """Delete a memo"""
        pass
