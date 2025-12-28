"""Pytest configuration and shared fixtures for testing."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.infrastructure.adapters.secondary.persistence.models import Base, User
from src.infrastructure.adapters.secondary.persistence.database import async_session_factory
from src.configuration.config import Settings

# Domain models
from src.domain.model.memo.memo import Memo
from src.domain.model.task.task_log import TaskLog
from src.domain.model.auth.user import User as DomainUser
from src.domain.model.auth.api_key import APIKey

# Repository implementations
from src.infrastructure.adapters.secondary.persistence.sql_memo_repository import SqlAlchemyMemoRepository
from src.infrastructure.adapters.secondary.persistence.sql_task_repository import SqlAlchemyTaskRepository
from src.infrastructure.adapters.secondary.persistence.sql_user_repository import SqlAlchemyUserRepository
from src.infrastructure.adapters.secondary.persistence.sql_api_key_repository import SqlAlchemyAPIKeyRepository

# DI Container
from src.configuration.di_container import DIContainer


# --- Database Fixtures ---

@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


# --- User Fixtures ---

@pytest.fixture
def test_user() -> User:
    """Create a test user (DB model)."""
    return User(
        id="user_123",
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User",
        is_active=True,
    )


@pytest.fixture
def test_domain_user() -> DomainUser:
    """Create a test user (Domain model)."""
    return DomainUser(
        id="user_123",
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User",
        is_active=True,
    )


@pytest.fixture
def test_tenant() -> dict:
    """Create a test tenant."""
    return {
        "id": "tenant_123",
        "name": "Test Tenant",
        "description": "A test tenant",
        "owner_id": "user_123",
        "plan": "free",
    }


@pytest.fixture
def test_project() -> dict:
    """Create a test project."""
    return {
        "id": "proj_123",
        "tenant_id": "tenant_123",
        "name": "Test Project",
        "description": "A test project",
        "owner_id": "user_123",
    }


# --- Repository Fixtures ---

@pytest.fixture
def memo_repository(test_db):
    """Create a memo repository for testing."""
    return SqlAlchemyMemoRepository(test_db)


@pytest.fixture
def task_repository(test_db):
    """Create a task repository for testing."""
    return SqlAlchemyTaskRepository(test_db)


@pytest.fixture
def user_repository(test_db):
    """Create a user repository for testing."""
    return SqlAlchemyUserRepository(test_db)


@pytest.fixture
def api_key_repository(test_db):
    """Create an API key repository for testing."""
    return SqlAlchemyAPIKeyRepository(test_db)


# --- DI Container Fixture ---

@pytest.fixture
def di_container(test_db, mock_graphiti_client):
    """Create a DI container for testing."""
    return DIContainer(test_db, graph_service=mock_graphiti_client)


# --- Domain Model Fixtures ---

@pytest.fixture
def test_memo() -> Memo:
    """Create a test memo (Domain model)."""
    return Memo(
        id="memo_123",
        content="Test memo content",
        user_id="user_123",
        visibility="PRIVATE",
        tags=["test", "fixture"],
    )


@pytest.fixture
def test_task_log() -> TaskLog:
    """Create a test task log (Domain model)."""
    return TaskLog(
        id="task_123",
        group_id="group_123",
        task_type="test_task",
        status="PENDING",
        payload={"test": "data"},
    )


@pytest.fixture
def test_api_key() -> APIKey:
    """Create a test API key (Domain model)."""
    return APIKey(
        id="key_123",
        user_id="user_123",
        key_hash="hashed_key",
        name="Test Key",
        permissions=["read", "write"],
    )


# --- Graphiti Mock Fixtures ---

@pytest.fixture
def mock_graphiti_client():
    """Create a mock Graphiti client."""
    client = Mock()
    client.driver = Mock()
    client.driver.execute_query = AsyncMock()

    # Mock add_episode method
    client.add_episode = AsyncMock()

    # Mock search_ method
    client.search_ = AsyncMock(
        return_value=Mock(
            episodes=[],
            nodes=[],
        )
    )

    # Mock build_indices_and_constraints
    client.build_indices_and_constraints = AsyncMock()

    # Mock close
    client.close = AsyncMock()

    return client


@pytest.fixture
def mock_graph_service():
    """Create a mock graph service port."""
    service = Mock()
    service.add_episode = AsyncMock()
    service.delete_episode_by_memory_id = AsyncMock()
    service.search = AsyncMock(return_value=[])
    return service


# --- FastAPI Test Client Fixtures ---

@pytest.fixture
def test_app(mock_graphiti_client):
    """Create a test FastAPI application."""
    from src.infrastructure.adapters.primary.web.main import create_app
    from src.infrastructure.adapters.secondary.persistence.models import User

    app = create_app()

    # Override dependencies
    from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client
    from src.infrastructure.adapters.primary.web.dependencies import get_current_user

    async def override_get_graphiti_client():
        return mock_graphiti_client

    async def override_get_current_user():
        # Create a test user directly instead of calling fixture
        return User(
            id="user_123",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            is_active=True,
        )

    app.dependency_overrides[get_graphiti_client] = override_get_graphiti_client
    app.dependency_overrides[get_current_user] = override_get_current_user

    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


# --- Mock Queue Service ---

@pytest.fixture
def mock_queue_service():
    """Create a mock queue service."""
    queue = Mock()
    queue.initialize = AsyncMock()
    queue.close = AsyncMock()
    queue.add_episode = AsyncMock()
    return queue


# --- Test Data Helpers ---

@pytest.fixture
def sample_episode_data() -> dict:
    """Sample episode data for testing."""
    return {
        "name": "Test Episode",
        "content": "This is a test episode content.",
        "source_description": "text",
        "episode_type": "text",
        "project_id": "proj_123",
        "tenant_id": "tenant_123",
        "user_id": "user_123",
    }


@pytest.fixture
def sample_memory_data() -> dict:
    """Sample memory data for testing."""
    return {
        "project_id": "proj_123",
        "title": "Test Memory",
        "content": "This is test memory content.",
        "author_id": "user_123",
        "tenant_id": "tenant_123",
        "content_type": "text",
        "tags": ["tag1", "tag2"],
        "is_public": False,
    }


@pytest.fixture
def sample_entity_data() -> dict:
    """Sample entity data for testing."""
    return {
        "uuid": "entity_123",
        "name": "TestEntity",
        "entity_type": "Organization",
        "summary": "A test organization",
        "tenant_id": "tenant_123",
        "project_id": "proj_123",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_memo_create_data() -> dict:
    """Sample memo creation data."""
    return {
        "content": "Test memo content",
        "visibility": "PRIVATE",
        "tags": ["test", "sample"],
    }


# --- Async Event Loop Fixture ---

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
