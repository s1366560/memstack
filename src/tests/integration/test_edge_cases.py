"""
Integration tests for edge cases and boundary conditions.
"""

import pytest
from datetime import datetime, timedelta, timezone
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
class TestEdgeCases:
    """Integration tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_cascade_delete_tenant_deletes_projects(self, test_db: AsyncSession):
        """Test that deleting a tenant requires explicit deletion of projects."""
        from sqlalchemy import select, delete

        # Create owner
        owner = User(
            id="edge_owner",
            email="edge@example.com",
            password_hash="hashed",
            name="Edge Owner",
        )
        test_db.add(owner)

        # Create tenant
        tenant = Tenant(
            id="edge_tenant",
            name="Edge Tenant",
            description="A tenant for edge case testing",
            owner_id="edge_owner",
            plan="free",
        )
        test_db.add(tenant)

        # Create project
        project = Project(
            id="edge_proj",
            tenant_id="edge_tenant",
            name="Edge Project",
            owner_id="edge_owner",
        )
        test_db.add(project)
        await test_db.commit()

        # Verify project exists
        proj_result = await test_db.execute(select(Project).where(Project.id == "edge_proj"))
        assert proj_result.scalar_one_or_none() is not None

        # Delete project first (foreign key constraint)
        await test_db.execute(delete(Project).where(Project.id == "edge_proj"))

        # Delete tenant
        await test_db.execute(delete(Tenant).where(Tenant.id == "edge_tenant"))
        await test_db.commit()

        # Verify both are deleted
        proj_result = await test_db.execute(select(Project).where(Project.id == "edge_proj"))
        assert proj_result.scalar_one_or_none() is None

        tenant_result = await test_db.execute(select(Tenant).where(Tenant.id == "edge_tenant"))
        assert tenant_result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_memo_with_tags_array_operations(self, test_db: AsyncSession):
        """Test memo tag array operations."""
        from sqlalchemy import select

        # Create memo with multiple tags
        memo = Memo(
            id="memo_tags",
            content="Tagged content",
            user_id="user_tags",
            visibility="PRIVATE",
            tags=["python", "fastapi", "testing", "async"]
        )
        test_db.add(memo)
        await test_db.commit()

        # Retrieve and verify
        result = await test_db.execute(select(Memo).where(Memo.id == "memo_tags"))
        retrieved = result.scalar_one()

        assert len(retrieved.tags) == 4
        assert "python" in retrieved.tags
        assert "async" in retrieved.tags

    @pytest.mark.asyncio
    async def test_task_with_complex_payload(self, test_db: AsyncSession):
        """Test task with nested and complex payload structure."""
        from sqlalchemy import select

        complex_payload = {
            "episode_data": {
                "uuid": "ep_123",
                "content": "Test content",
                "metadata": {
                    "source": "api",
                    "timestamp": datetime.utcnow().isoformat(),
                    "nested": {
                        "key": "value",
                        "array": [1, 2, 3]
                    }
                }
            },
            "config": {
                "retries": 3,
                "timeout": 30
            }
        }

        task = TaskLog(
            id="task_complex",
            group_id="group_complex",
            task_type="complex_task",
            status="PENDING",
            payload=complex_payload,
            entity_id="entity_123",
            entity_type="episode"
        )
        test_db.add(task)
        await test_db.commit()

        # Retrieve and verify
        result = await test_db.execute(select(TaskLog).where(TaskLog.id == "task_complex"))
        retrieved = result.scalar_one()

        assert retrieved.payload == complex_payload
        assert retrieved.payload["episode_data"]["metadata"]["nested"]["array"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_api_key_expiration_boundary(self, test_db: AsyncSession):
        """Test API key expiration at boundary conditions."""
        from sqlalchemy import select

        # Key expiring in 1 second
        expires_soon = datetime.now(timezone.utc) + timedelta(seconds=1)
        key1 = APIKey(
            id="key_expiring_soon",
            user_id="user_boundary",
            key_hash="hash_1",
            name="Expiring Soon",
            expires_at=expires_soon
        )

        # Key that just expired
        just_expired = datetime.now(timezone.utc) - timedelta(seconds=1)
        key2 = APIKey(
            id="key_just_expired",
            user_id="user_boundary",
            key_hash="hash_2",
            name="Just Expired",
            expires_at=just_expired
        )

        test_db.add(key1)
        test_db.add(key2)
        await test_db.commit()

        # Verify both are stored correctly
        result1 = await test_db.execute(select(APIKey).where(APIKey.id == "key_expiring_soon"))
        retrieved1 = result1.scalar_one()
        assert retrieved1.expires_at is not None

        result2 = await test_db.execute(select(APIKey).where(APIKey.id == "key_just_expired"))
        retrieved2 = result2.scalar_one()
        assert retrieved2.expires_at is not None

    @pytest.mark.asyncio
    async def test_memory_with_empty_relationships(self, test_db: AsyncSession):
        """Test memory with empty entities and relationships arrays."""
        from sqlalchemy import select

        memory = Memory(
            id="mem_empty",
            project_id="proj_empty",
            title="Memory with empty arrays",
            content="Content",
            author_id="user_empty",
            content_type="text",
            tags=[],
            entities=[],
            relationships=[],
            version=1
        )
        test_db.add(memory)
        await test_db.commit()

        # Retrieve and verify
        result = await test_db.execute(select(Memory).where(Memory.id == "mem_empty"))
        retrieved = result.scalar_one()

        assert retrieved.tags == []
        assert retrieved.entities == []
        assert retrieved.relationships == []

    @pytest.mark.asyncio
    async def test_task_status_transitions(self, test_db: AsyncSession):
        """Test task status transition workflow."""
        from sqlalchemy import select

        # Create task in PENDING state
        task = TaskLog(
            id="task_workflow",
            group_id="group_workflow",
            task_type="workflow_task",
            status="PENDING"
        )
        test_db.add(task)
        await test_db.commit()

        # Transition to PROCESSING
        result = await test_db.execute(select(TaskLog).where(TaskLog.id == "task_workflow"))
        task = result.scalar_one()
        task.status = "PROCESSING"
        task.started_at = datetime.utcnow()
        await test_db.commit()

        # Verify transition
        result = await test_db.execute(select(TaskLog).where(TaskLog.id == "task_workflow"))
        task = result.scalar_one()
        assert task.status == "PROCESSING"
        assert task.started_at is not None

        # Transition to COMPLETED
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()
        await test_db.commit()

        # Verify final state
        result = await test_db.execute(select(TaskLog).where(TaskLog.id == "task_workflow"))
        task = result.scalar_one()
        assert task.status == "COMPLETED"
        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_concurrent_memo_updates(self, test_db: AsyncSession):
        """Test handling of rapid memo updates."""
        from sqlalchemy import select

        # Create initial memo
        memo = Memo(
            id="memo_concurrent",
            content="Original",
            user_id="user_concurrent",
            visibility="PRIVATE"
        )
        test_db.add(memo)
        await test_db.commit()

        # Simulate rapid updates
        for i in range(5):
            result = await test_db.execute(select(Memo).where(Memo.id == "memo_concurrent"))
            memo = result.scalar_one()
            memo.content = f"Update {i}"
            memo.tags = [f"tag{j}" for j in range(i)]
            await test_db.commit()

        # Verify final state
        result = await test_db.execute(select(Memo).where(Memo.id == "memo_concurrent"))
        final = result.scalar_one()
        assert final.content == "Update 4"
        assert len(final.tags) == 4

    @pytest.mark.asyncio
    async def test_long_text_fields(self, test_db: AsyncSession):
        """Test handling of very long text fields."""
        from sqlalchemy import select

        long_content = "x" * 10000  # 10k characters
        long_name = "y" * 500

        memo = Memo(
            id="memo_long",
            content=long_content,
            user_id="user_long",
            visibility="PRIVATE",
            tags=["long_content_test"]
        )
        test_db.add(memo)
        await test_db.commit()

        # Retrieve and verify
        result = await test_db.execute(select(Memo).where(Memo.id == "memo_long"))
        retrieved = result.scalar_one()
        assert len(retrieved.content) == 10000

        tenant = Tenant(
            id="tenant_long",
            name=long_name,
            description="A tenant with a very long name",
            owner_id="user_long",
            plan="free"
        )
        test_db.add(tenant)
        await test_db.commit()

        result = await test_db.execute(select(Tenant).where(Tenant.id == "tenant_long"))
        retrieved = result.scalar_one()
        assert len(retrieved.name) == 500
