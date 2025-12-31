"""
Use case for listing memos for a user.
"""

from dataclasses import dataclass
from typing import List

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository


@dataclass
class ListMemosQuery:
    """Query to list memos"""
    user_id: str
    limit: int = 20
    offset: int = 0


class ListMemosUseCase:
    """Use case for listing user memos"""

    def __init__(self, memo_repository: MemoRepository):
        self._memo_repo = memo_repository

    async def execute(self, query: ListMemosQuery) -> List[Memo]:
        """
        List memos for a user.

        Args:
            query: ListMemosQuery with user_id and pagination

        Returns:
            List of Memo entities
        """
        return await self._memo_repo.find_by_user(
            user_id=query.user_id,
            limit=query.limit,
            offset=query.offset
        )
