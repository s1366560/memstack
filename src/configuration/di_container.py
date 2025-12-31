"""
Simple Dependency Injection Container for use cases.

This container provides fully constructed use cases with their dependencies,
following the Dependency Inversion Principle.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# Memo use cases
from src.application.use_cases.memo import (
    CreateMemoUseCase,
    GetMemoUseCase,
    ListMemosUseCase,
    UpdateMemoUseCase,
    DeleteMemoUseCase,
)
from src.infrastructure.adapters.secondary.persistence.sql_memo_repository import SqlAlchemyMemoRepository

# Memory use cases
from src.application.use_cases.memory.create_memory import CreateMemoryUseCase as MemCreateMemoryUseCase
from src.application.use_cases.memory.get_memory import GetMemoryUseCase as MemGetMemoryUseCase
from src.application.use_cases.memory.list_memories import ListMemoriesUseCase
from src.application.use_cases.memory.delete_memory import DeleteMemoryUseCase as MemDeleteMemoryUseCase
from src.domain.ports.repositories.memory_repository import MemoryRepository
from src.infrastructure.adapters.secondary.persistence.sql_memory_repository import SqlAlchemyMemoryRepository

# Task use cases
from src.application.use_cases.task import (
    CreateTaskUseCase,
    GetTaskUseCase,
    ListTasksUseCase,
    UpdateTaskUseCase,
)
from src.infrastructure.adapters.secondary.persistence.sql_task_repository import SqlAlchemyTaskRepository


class DIContainer:
    """
    Dependency Injection Container for use cases.

    This container creates use cases with their dependencies injected,
    allowing routers to depend on abstractions (use cases) rather than
    concrete implementations.
    """

    def __init__(self, db: AsyncSession, graph_service=None):
        self._db = db
        self._graph_service = graph_service

    # === Memo Use Cases ===

    def create_memo_use_case(self) -> CreateMemoUseCase:
        """Get CreateMemoUseCase with dependencies injected"""
        memo_repo = SqlAlchemyMemoRepository(self._db)
        return CreateMemoUseCase(memo_repo)

    def get_memo_use_case(self) -> GetMemoUseCase:
        """Get GetMemoUseCase with dependencies injected"""
        memo_repo = SqlAlchemyMemoRepository(self._db)
        return GetMemoUseCase(memo_repo)

    def list_memos_use_case(self) -> ListMemosUseCase:
        """Get ListMemosUseCase with dependencies injected"""
        memo_repo = SqlAlchemyMemoRepository(self._db)
        return ListMemosUseCase(memo_repo)

    def update_memo_use_case(self) -> UpdateMemoUseCase:
        """Get UpdateMemoUseCase with dependencies injected"""
        memo_repo = SqlAlchemyMemoRepository(self._db)
        return UpdateMemoUseCase(memo_repo)

    def delete_memo_use_case(self) -> DeleteMemoUseCase:
        """Get DeleteMemoUseCase with dependencies injected"""
        memo_repo = SqlAlchemyMemoRepository(self._db)
        return DeleteMemoUseCase(memo_repo)

    # === Memory Use Cases ===

    def create_memory_use_case(self) -> MemCreateMemoryUseCase:
        """Get CreateMemoryUseCase with dependencies injected"""
        memory_repo = SqlAlchemyMemoryRepository(self._db)
        if not self._graph_service:
            raise ValueError("graph_service is required for CreateMemoryUseCase")
        return MemCreateMemoryUseCase(memory_repo, self._graph_service)

    def get_memory_use_case(self) -> MemGetMemoryUseCase:
        """Get GetMemoryUseCase with dependencies injected"""
        memory_repo = SqlAlchemyMemoryRepository(self._db)
        return MemGetMemoryUseCase(memory_repo)

    def list_memories_use_case(self) -> ListMemoriesUseCase:
        """Get ListMemoriesUseCase with dependencies injected"""
        memory_repo = SqlAlchemyMemoryRepository(self._db)
        return ListMemoriesUseCase(memory_repo)

    def delete_memory_use_case(self) -> MemDeleteMemoryUseCase:
        """Get DeleteMemoryUseCase with dependencies injected"""
        memory_repo = SqlAlchemyMemoryRepository(self._db)
        if not self._graph_service:
            raise ValueError("graph_service is required for DeleteMemoryUseCase")
        return MemDeleteMemoryUseCase(memory_repo, self._graph_service)

    # === Task Use Cases ===

    def create_task_use_case(self) -> CreateTaskUseCase:
        """Get CreateTaskUseCase with dependencies injected"""
        task_repo = SqlAlchemyTaskRepository(self._db)
        return CreateTaskUseCase(task_repo)

    def get_task_use_case(self) -> GetTaskUseCase:
        """Get GetTaskUseCase with dependencies injected"""
        task_repo = SqlAlchemyTaskRepository(self._db)
        return GetTaskUseCase(task_repo)

    def list_tasks_use_case(self) -> ListTasksUseCase:
        """Get ListTasksUseCase with dependencies injected"""
        task_repo = SqlAlchemyTaskRepository(self._db)
        return ListTasksUseCase(task_repo)

    def update_task_use_case(self) -> UpdateTaskUseCase:
        """Get UpdateTaskUseCase with dependencies injected"""
        task_repo = SqlAlchemyTaskRepository(self._db)
        return UpdateTaskUseCase(task_repo)
