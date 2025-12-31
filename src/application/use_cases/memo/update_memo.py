"""
Use case for updating a memo.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository


@dataclass
class UpdateMemoCommand:
    """Command to update a memo"""
    memo_id: str
    user_id: str  # For authorization
    content: Optional[str] = None
    visibility: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateMemoUseCase:
    """Use case for updating memos"""

    def __init__(self, memo_repository: MemoRepository):
        self._memo_repo = memo_repository

    async def execute(self, command: UpdateMemoCommand) -> Optional[Memo]:
        """
        Update a memo.

        Args:
            command: UpdateMemoCommand with updates

        Returns:
            Updated Memo if found and authorized, None otherwise
        """
        # Get existing memo
        memo = await self._memo_repo.find_by_id(command.memo_id)

        if not memo:
            return None

        # Authorization: only owner can update
        if memo.user_id != command.user_id:
            return None

        # Update fields
        if command.content is not None:
            memo.content = command.content
        if command.visibility is not None:
            memo.visibility = command.visibility
        if command.tags is not None:
            memo.tags = command.tags

        memo.updated_at = datetime.utcnow()

        # Save changes
        await self._memo_repo.save(memo)
        return memo
