"""
Use case for creating a new memo.
"""

from dataclasses import dataclass
from typing import List

from src.domain.model.memo.memo import Memo
from src.domain.ports.repositories.memo_repository import MemoRepository


@dataclass
class CreateMemoCommand:
    """Command to create a new memo"""
    content: str
    user_id: str
    visibility: str = "PRIVATE"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CreateMemoUseCase:
    """Use case for creating memos"""

    def __init__(self, memo_repository: MemoRepository):
        self._memo_repo = memo_repository

    async def execute(self, command: CreateMemoCommand) -> Memo:
        """
        Create a new memo.

        Args:
            command: CreateMemoCommand with memo details

        Returns:
            Created Memo entity
        """
        memo = Memo(
            content=command.content,
            user_id=command.user_id,
            visibility=command.visibility,
            tags=command.tags,
        )

        await self._memo_repo.save(memo)
        return memo
