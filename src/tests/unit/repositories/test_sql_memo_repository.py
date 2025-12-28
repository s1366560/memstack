"""
Unit tests for SqlAlchemyMemoRepository.
"""

import pytest
from datetime import datetime

from src.domain.model.memo.memo import Memo
from src.infrastructure.adapters.secondary.persistence.sql_memo_repository import SqlAlchemyMemoRepository


@pytest.mark.unit
class TestSqlAlchemyMemoRepository:
    """Test cases for SqlAlchemyMemoRepository"""

    @pytest.mark.asyncio
    async def test_save_new_memo(self, test_db):
        """Test saving a new memo to the database"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo = Memo(
            id="memo_test_1",
            content="Test content for new memo",
            user_id="user_123",
            visibility="PRIVATE",
            tags=["test", "new"]
        )

        # Act
        await repo.save(memo)
        await test_db.commit()

        # Assert
        result = await repo.find_by_id("memo_test_1")
        assert result is not None
        assert result.id == "memo_test_1"
        assert result.content == "Test content for new memo"
        assert result.user_id == "user_123"
        assert result.visibility == "PRIVATE"
        assert result.tags == ["test", "new"]

    @pytest.mark.asyncio
    async def test_save_update_existing_memo(self, test_db):
        """Test updating an existing memo"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo = Memo(
            id="memo_test_2",
            content="Original content",
            user_id="user_123",
            visibility="PRIVATE",
            tags=["original"]
        )
        await repo.save(memo)
        await test_db.commit()

        # Act - Update the memo
        memo.content = "Updated content"
        memo.visibility = "PUBLIC"
        memo.tags = ["updated"]
        memo.updated_at = datetime.utcnow()
        await repo.save(memo)
        await test_db.commit()

        # Assert
        result = await repo.find_by_id("memo_test_2")
        assert result is not None
        assert result.content == "Updated content"
        assert result.visibility == "PUBLIC"
        assert result.tags == ["updated"]

    @pytest.mark.asyncio
    async def test_find_by_id_success(self, test_db):
        """Test finding a memo by ID"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo = Memo(
            id="memo_test_3",
            content="Find me by ID",
            user_id="user_123",
            visibility="PRIVATE"
        )
        await repo.save(memo)
        await test_db.commit()

        # Act
        result = await repo.find_by_id("memo_test_3")

        # Assert
        assert result is not None
        assert result.id == "memo_test_3"
        assert result.content == "Find me by ID"

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, test_db):
        """Test finding a non-existent memo by ID"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)

        # Act
        result = await repo.find_by_id("nonexistent_memo")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_user(self, test_db):
        """Test finding all memos for a user"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo1 = Memo(
            id="memo_test_4a",
            content="User memo 1",
            user_id="user_123",
            visibility="PRIVATE"
        )
        memo2 = Memo(
            id="memo_test_4b",
            content="User memo 2",
            user_id="user_123",
            visibility="PUBLIC"
        )
        memo3 = Memo(
            id="memo_test_4c",
            content="Different user memo",
            user_id="user_456",
            visibility="PRIVATE"
        )
        await repo.save(memo1)
        await repo.save(memo2)
        await repo.save(memo3)
        await test_db.commit()

        # Act
        results = await repo.find_by_user("user_123")

        # Assert
        assert len(results) == 2
        memo_ids = [m.id for m in results]
        assert "memo_test_4a" in memo_ids
        assert "memo_test_4b" in memo_ids
        assert "memo_test_4c" not in memo_ids

    @pytest.mark.asyncio
    async def test_find_by_user_with_pagination(self, test_db):
        """Test finding memos for a user with pagination"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        for i in range(5):
            memo = Memo(
                id=f"memo_test_5_{i}",
                content=f"Memo {i}",
                user_id="user_123",
                visibility="PRIVATE"
            )
            await repo.save(memo)
        await test_db.commit()

        # Act
        results = await repo.find_by_user("user_123", limit=2, offset=2)

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_visibility(self, test_db):
        """Test listing memos by visibility level"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo1 = Memo(
            id="memo_test_6a",
            content="Private memo",
            user_id="user_123",
            visibility="PRIVATE"
        )
        memo2 = Memo(
            id="memo_test_6b",
            content="Public memo",
            user_id="user_123",
            visibility="PUBLIC"
        )
        memo3 = Memo(
            id="memo_test_6c",
            content="Another private memo",
            user_id="user_123",
            visibility="PRIVATE"
        )
        await repo.save(memo1)
        await repo.save(memo2)
        await repo.save(memo3)
        await test_db.commit()

        # Act
        results = await repo.list_by_visibility("user_123", "PRIVATE")

        # Assert
        assert len(results) == 2
        memo_ids = [m.id for m in results]
        assert "memo_test_6a" in memo_ids
        assert "memo_test_6c" in memo_ids
        assert "memo_test_6b" not in memo_ids

    @pytest.mark.asyncio
    async def test_delete_memo(self, test_db):
        """Test deleting a memo"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        memo = Memo(
            id="memo_test_7",
            content="Memo to delete",
            user_id="user_123",
            visibility="PRIVATE"
        )
        await repo.save(memo)
        await test_db.commit()

        # Verify it exists
        assert await repo.find_by_id("memo_test_7") is not None

        # Act
        await repo.delete("memo_test_7")
        await test_db.commit()

        # Assert
        result = await repo.find_by_id("memo_test_7")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memo(self, test_db):
        """Test deleting a non-existent memo (should not raise error)"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)

        # Act - Should not raise an error
        await repo.delete("nonexistent_memo")
        await test_db.commit()

        # Assert - No exception raised

    @pytest.mark.asyncio
    async def test_to_domain_conversion(self, test_db):
        """Test conversion from DB model to domain model"""
        # Arrange
        repo = SqlAlchemyMemoRepository(test_db)
        created_at = datetime.utcnow()
        memo = Memo(
            id="memo_test_8",
            content="Test conversion",
            user_id="user_123",
            visibility="PROTECTED",
            tags=["conversion", "test"],
            created_at=created_at
        )
        await repo.save(memo)
        await test_db.commit()

        # Act
        result = await repo.find_by_id("memo_test_8")

        # Assert
        assert result is not None
        assert isinstance(result, Memo)
        assert result.id == "memo_test_8"
        assert result.content == "Test conversion"
        assert result.user_id == "user_123"
        assert result.visibility == "PROTECTED"
        assert result.tags == ["conversion", "test"]
        assert isinstance(result.created_at, datetime)
