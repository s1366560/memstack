"""
Use case for getting a memo by ID.
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository


@dataclass
class GetMemoQuery:
    """Query to get a memo by ID"""
    memo_id: str
    user_id: str  # For authorization check


class GetMemoUseCase:
    """Use case for retrieving a single memo"""

    def __init__(self, memo_repository: MemoRepository):
        self._memo_repo = memo_repository

    async def execute(self, query: GetMemoQuery) -> Optional[Memo]:
        """
        Get a memo by ID.

        Args:
            query: GetMemoQuery containing memo_id and user_id

        Returns:
            Memo if found and belongs to user, None otherwise
        """
        memo = await self._memo_repo.find_by_id(query.memo_id)

        # Authorization: only return memo if it belongs to the user
        if memo and memo.user_id == query.user_id:
            return memo

        return None
