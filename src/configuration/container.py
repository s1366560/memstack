from typing import Callable, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from graphiti_core import Graphiti
import redis.asyncio as redis

from src.infrastructure.adapters.secondary.sql_memory_repository import SqlAlchemyMemoryRepository
from src.infrastructure.adapters.secondary.graphiti.graphiti_adapter import GraphitiAdapter
from src.infrastructure.adapters.secondary.queue_adapter import RedisQueueAdapter
from src.application.use_cases.memory.create_memory import CreateMemoryUseCase
from src.application.use_cases.memory.search_memory import SearchMemoryUseCase
from src.application.use_cases.memory.delete_memory import DeleteMemoryUseCase
from src.configuration.config import get_settings

class DIContainer:
    def __init__(self, session_factory: Callable[[], AsyncSession], graphiti_client: Graphiti, redis_client: Optional[redis.Redis] = None):
        self.session_factory = session_factory
        self.graphiti_client = graphiti_client
        self.redis_client = redis_client

    def memory_repository(self, session: AsyncSession) -> SqlAlchemyMemoryRepository:
        return SqlAlchemyMemoryRepository(session)

    def queue_port(self) -> RedisQueueAdapter:
        # We instantiate the adapter directly. It will handle its own redis connection if not provided,
        # or we can pass the one from init.
        return RedisQueueAdapter(self.redis_client)

    def graph_service(self) -> GraphitiAdapter:
        return GraphitiAdapter(client=self.graphiti_client, queue_port=self.queue_port())

    def create_memory_use_case(self, session: AsyncSession) -> CreateMemoryUseCase:
        return CreateMemoryUseCase(
            memory_repository=self.memory_repository(session),
            graph_service=self.graph_service()
        )

    def search_memory_use_case(self) -> SearchMemoryUseCase:
        return SearchMemoryUseCase(
            graph_service=self.graph_service()
        )

    def delete_memory_use_case(self, session: AsyncSession) -> DeleteMemoryUseCase:
        return DeleteMemoryUseCase(
            memory_repository=self.memory_repository(session),
            graph_service=self.graph_service()
        )
