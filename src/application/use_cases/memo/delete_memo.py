"""
Use case for deleting a memo.
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository


@dataclass
class DeleteMemoCommand:
    """Command to delete a memo"""
    memo_id: str
    user_id: str  # For authorization


class DeleteMemoUseCase:
    """Use case for deleting memos"""

    def __init__(self, memo_repository: MemoRepository):
        self._memo_repo = memo_repository

    async def execute(self, command: DeleteMemoCommand) -> bool:
        """
        Delete a memo.

        Args:
            command: DeleteMemoCommand with memo_id and user_id

        Returns:
            True if deleted, False if not found or unauthorized
        """
        # Get existing memo
        memo = await self._memo_repo.find_by_id(command.memo_id)

        if not memo:
            return False

        # Authorization: only owner can delete
        if memo.user_id != command.user_id:
            return False

        # Delete
        await self._memo_repo.delete(command.memo_id)
        return True
