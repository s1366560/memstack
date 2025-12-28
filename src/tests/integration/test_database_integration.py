"""Integration tests for database repositories."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.adapters.secondary.persistence.models import (
    User,
    APIKey,
    Tenant,
    Project,
    Memory,
    Memo,
    TaskLog,
)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_user(self, test_db: AsyncSession):
        """Test creating and retrieving a user."""
        # Create user
        user = User(
            id="test_user_123",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            is_active=True,
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Retrieve user
        from sqlalchemy import select

        result = await test_db.execute(select(User).where(User.id == "test_user_123"))
        retrieved_user = result.scalar_one()

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.name == "Test User"

    @pytest.mark.asyncio
    async def test_user_with_api_keys(self, test_db: AsyncSession):
        """Test creating a user with API keys."""
        # Create user
        user = User(
            id="user_with_keys",
            email="keys@example.com",
            password_hash="hashed",
            name="Key User",
        )
        test_db.add(user)

        # Create API keys
        key1 = APIKey(
            id="key_1",
            key_hash="hash1",
            name="First Key",
            user_id="user_with_keys",
        )
        key2 = APIKey(
            id="key_2",
            key_hash="hash2",
            name="Second Key",
            user_id="user_with_keys",
        )
        test_db.add(key1)
        test_db.add(key2)
        await test_db.commit()

        # Retrieve and verify with eager loading
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await test_db.execute(
            select(User)
            .where(User.id == "user_with_keys")
            .options(selectinload(User.api_keys))
        )
        user = result.scalar_one()

        assert len(user.api_keys) == 2

    @pytest.mark.asyncio
    async def test_tenant_with_projects(self, test_db: AsyncSession):
        """Test creating a tenant with projects."""
        # Create owner
        owner = User(
            id="tenant_owner",
            email="owner@example.com",
            password_hash="hashed",
            name="Owner",
        )
        test_db.add(owner)

        # Create tenant
        tenant = Tenant(
            id="tenant_1",
            name="Test Tenant",
            description="A test tenant",
            owner_id="tenant_owner",
            plan="free",
        )
        test_db.add(tenant)

        # Create projects
        project1 = Project(
            id="proj_1",
            tenant_id="tenant_1",
            name="Project 1",
            owner_id="tenant_owner",
        )
        project2 = Project(
            id="proj_2",
            tenant_id="tenant_1",
            name="Project 2",
            owner_id="tenant_owner",
        )
        test_db.add(project1)
        test_db.add(project2)
        await test_db.commit()

        # Retrieve and verify with eager loading
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await test_db.execute(
            select(Tenant)
            .where(Tenant.id == "tenant_1")
            .options(selectinload(Tenant.projects))
        )
        tenant = result.scalar_one()

        assert len(tenant.projects) == 2

    @pytest.mark.asyncio
    async def test_memory_crud(self, test_db: AsyncSession):
        """Test Memory CRUD operations."""
        # Create user and project
        user = User(id="mem_user", email="mem@example.com", password_hash="hash", name="Mem User")
        project = Project(
            id="mem_proj",
            tenant_id="mem_tenant",
            name="Mem Project",
            owner_id="mem_user",
        )
        test_db.add(user)
        test_db.add(project)
        await test_db.commit()

        # Create memory
        memory = Memory(
            id="mem_1",
            project_id="mem_proj",
            title="Test Memory",
            content="Test content",
            author_id="mem_user",
            tags=["tag1", "tag2"],
        )
        test_db.add(memory)
        await test_db.commit()
        await test_db.refresh(memory)

        # Read memory
        from sqlalchemy import select

        result = await test_db.execute(select(Memory).where(Memory.id == "mem_1"))
        retrieved = result.scalar_one()

        assert retrieved.title == "Test Memory"
        assert retrieved.tags == ["tag1", "tag2"]

        # Update memory
        retrieved.title = "Updated Memory"
        await test_db.commit()
        await test_db.refresh(retrieved)

        assert retrieved.title == "Updated Memory"

        # Delete memory
        await test_db.delete(retrieved)
        await test_db.commit()

        result = await test_db.execute(select(Memory).where(Memory.id == "mem_1"))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_memo_crud(self, test_db: AsyncSession):
        """Test Memo CRUD operations."""
        # Create user
        user = User(id="memo_user", email="memo@example.com", password_hash="hash", name="Memo User")
        test_db.add(user)
        await test_db.commit()

        # Create memo
        memo = Memo(
            id="memo_1",
            content="Test memo content",
            user_id="memo_user",
            visibility="PRIVATE",
            tags=["important", "work"],
        )
        test_db.add(memo)
        await test_db.commit()
        await test_db.refresh(memo)

        # Read memo
        from sqlalchemy import select

        result = await test_db.execute(select(Memo).where(Memo.id == "memo_1"))
        retrieved = result.scalar_one()

        assert retrieved.content == "Test memo content"
        assert retrieved.visibility == "PRIVATE"

        # Update memo
        retrieved.content = "Updated memo"
        await test_db.commit()
        await test_db.refresh(retrieved)

        assert retrieved.content == "Updated memo"

        # Delete memo
        await test_db.delete(retrieved)
        await test_db.commit()

        result = await test_db.execute(select(Memo).where(Memo.id == "memo_1"))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_task_log_crud(self, test_db: AsyncSession):
        """Test TaskLog CRUD operations."""
        # Create task log
        task = TaskLog(
            id="task_1",
            group_id="test_group",
            task_type="process_episode",
            status="PENDING",
            entity_id="entity_123",
            entity_type="episode",
            payload={"episode_uuid": "ep_123"},
        )
        test_db.add(task)
        await test_db.commit()
        await test_db.refresh(task)

        # Read task
        from sqlalchemy import select

        result = await test_db.execute(select(TaskLog).where(TaskLog.id == "task_1"))
        retrieved = result.scalar_one()

        assert retrieved.task_type == "process_episode"
        assert retrieved.status == "PENDING"
        assert retrieved.payload == {"episode_uuid": "ep_123"}

        # Update task status
        retrieved.status = "PROCESSING"
        retrieved.started_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(retrieved)

        assert retrieved.status == "PROCESSING"
        assert retrieved.started_at is not None

        # Complete task
        retrieved.status = "COMPLETED"
        retrieved.completed_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(retrieved)

        assert retrieved.status == "COMPLETED"
        assert retrieved.completed_at is not None

    @pytest.mark.asyncio
    async def test_cascade_delete_user(self, test_db: AsyncSession):
        """Test cascade delete when user is deleted."""
        # Create user with API keys and memos
        user = User(id="cascade_user", email="cascade@example.com", password_hash="hash", name="Cascade")
        test_db.add(user)

        api_key = APIKey(
            id="cascade_key",
            key_hash="hash",
            name="Cascade Key",
            user_id="cascade_user",
        )
        test_db.add(api_key)

        memo = Memo(
            id="cascade_memo",
            content="Cascade memo",
            user_id="cascade_user",
        )
        test_db.add(memo)
        await test_db.commit()

        # Delete user (should cascade to API keys and memos)
        await test_db.delete(user)
        await test_db.commit()

        # Verify cascade
        from sqlalchemy import select

        api_key_result = await test_db.execute(
            select(APIKey).where(APIKey.user_id == "cascade_user")
        )
        assert api_key_result.scalar_one_or_none() is None

        memo_result = await test_db.execute(
            select(Memo).where(Memo.user_id == "cascade_user")
        )
        assert memo_result.scalar_one_or_none() is None


@pytest.mark.integration
class TestDatabaseQueries:
    """Integration tests for complex database queries."""

    @pytest.mark.asyncio
    async def test_query_memories_by_project(self, test_db: AsyncSession):
        """Test querying memories by project."""
        # Create test data
        user = User(id="query_user", email="query@example.com", password_hash="hash", name="Query")
        project = Project(
            id="query_proj",
            tenant_id="query_tenant",
            name="Query Project",
            owner_id="query_user",
        )
        test_db.add(user)
        test_db.add(project)

        # Create multiple memories
        for i in range(5):
            memory = Memory(
                id=f"query_mem_{i}",
                project_id="query_proj",
                title=f"Memory {i}",
                content=f"Content {i}",
                author_id="query_user",
            )
            test_db.add(memory)

        await test_db.commit()

        # Query memories by project
        from sqlalchemy import select

        result = await test_db.execute(
            select(Memory).where(Memory.project_id == "query_proj").order_by(Memory.created_at)
        )
        memories = result.scalars().all()

        assert len(memories) == 5

    @pytest.mark.asyncio
    async def test_query_tasks_by_status(self, test_db: AsyncSession):
        """Test querying tasks by status."""
        # Create tasks with different statuses
        for i, status in enumerate(["PENDING", "PROCESSING", "COMPLETED", "FAILED"]):
            task = TaskLog(
                id=f"status_task_{i}",
                group_id="status_group",
                task_type=f"task_{i}",
                status=status,
            )
            test_db.add(task)

        await test_db.commit()

        # Query completed tasks
        from sqlalchemy import select, func

        result = await test_db.execute(
            select(TaskLog.status, func.count(TaskLog.id))
            .group_by(TaskLog.status)
            .order_by(TaskLog.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}

        assert status_counts.get("PENDING") == 1
        assert status_counts.get("PROCESSING") == 1
        assert status_counts.get("COMPLETED") == 1
        assert status_counts.get("FAILED") == 1
