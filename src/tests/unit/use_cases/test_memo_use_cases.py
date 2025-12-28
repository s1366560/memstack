"""
Unit tests for Memo use cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.domain.model.memo.memo import Memo
from src.application.use_cases.memo.create_memo import CreateMemoUseCase, CreateMemoCommand
from src.application.use_cases.memo.get_memo import GetMemoUseCase, GetMemoQuery
from src.application.use_cases.memo.list_memos import ListMemosUseCase, ListMemosQuery
from src.application.use_cases.memo.update_memo import UpdateMemoUseCase, UpdateMemoCommand
from src.application.use_cases.memo.delete_memo import DeleteMemoUseCase, DeleteMemoCommand


@pytest.mark.unit
class TestCreateMemoUseCase:
    """Test cases for CreateMemoUseCase"""

    @pytest.mark.asyncio
    async def test_create_memo_with_all_fields(self):
        """Test creating a memo with all fields provided"""
        # Arrange
        mock_repo = Mock()
        mock_repo.save = AsyncMock()

        use_case = CreateMemoUseCase(mock_repo)
        command = CreateMemoCommand(
            content="Test content",
            user_id="user_123",
            visibility="PRIVATE",
            tags=["test", "example"]
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.content == "Test content"
        assert result.user_id == "user_123"
        assert result.visibility == "PRIVATE"
        assert result.tags == ["test", "example"]
        assert result.id is not None
        assert isinstance(result.created_at, datetime)
        mock_repo.save.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_create_memo_with_defaults(self):
        """Test creating a memo with default values"""
        # Arrange
        mock_repo = Mock()
        mock_repo.save = AsyncMock()

        use_case = CreateMemoUseCase(mock_repo)
        command = CreateMemoCommand(
            content="Test content",
            user_id="user_123"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.content == "Test content"
        assert result.visibility == "PRIVATE"  # Default
        assert result.tags == []  # Default
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_memo_with_none_tags(self):
        """Test creating a memo with None tags converts to empty list"""
        # Arrange
        mock_repo = Mock()
        mock_repo.save = AsyncMock()

        use_case = CreateMemoUseCase(mock_repo)
        command = CreateMemoCommand(
            content="Test content",
            user_id="user_123",
            tags=None
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.tags == []
        mock_repo.save.assert_called_once()


@pytest.mark.unit
class TestGetMemoUseCase:
    """Test cases for GetMemoUseCase"""

    @pytest.mark.asyncio
    async def test_get_memo_success(self):
        """Test getting a memo successfully"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Test content",
            user_id="user_123",
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)

        use_case = GetMemoUseCase(mock_repo)
        query = GetMemoQuery(memo_id="memo_123", user_id="user_123")

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result is not None
        assert result.id == "memo_123"
        assert result.content == "Test content"
        mock_repo.find_by_id.assert_called_once_with("memo_123")

    @pytest.mark.asyncio
    async def test_get_memo_not_found(self):
        """Test getting a non-existent memo"""
        # Arrange
        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=None)

        use_case = GetMemoUseCase(mock_repo)
        query = GetMemoQuery(memo_id="nonexistent", user_id="user_123")

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result is None
        mock_repo.find_by_id.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_memo_unauthorized_user(self):
        """Test getting a memo owned by another user"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Private content",
            user_id="user_456",  # Different user
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)

        use_case = GetMemoUseCase(mock_repo)
        query = GetMemoQuery(memo_id="memo_123", user_id="user_123")

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result is None  # Unauthorized access returns None
        mock_repo.find_by_id.assert_called_once_with("memo_123")


@pytest.mark.unit
class TestListMemosUseCase:
    """Test cases for ListMemosUseCase"""

    @pytest.mark.asyncio
    async def test_list_memos_default_pagination(self):
        """Test listing memos with default pagination"""
        # Arrange
        memos = [
            Memo(id="memo_1", content="Content 1", user_id="user_123"),
            Memo(id="memo_2", content="Content 2", user_id="user_123"),
        ]

        mock_repo = Mock()
        mock_repo.find_by_user = AsyncMock(return_value=memos)

        use_case = ListMemosUseCase(mock_repo)
        query = ListMemosQuery(user_id="user_123")

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result) == 2
        assert result[0].id == "memo_1"
        assert result[1].id == "memo_2"
        mock_repo.find_by_user.assert_called_once_with(user_id="user_123", limit=20, offset=0)

    @pytest.mark.asyncio
    async def test_list_memos_with_pagination(self):
        """Test listing memos with custom pagination"""
        # Arrange
        memos = [
            Memo(id="memo_1", content="Content 1", user_id="user_123"),
        ]

        mock_repo = Mock()
        mock_repo.find_by_user = AsyncMock(return_value=memos)

        use_case = ListMemosUseCase(mock_repo)
        query = ListMemosQuery(user_id="user_123", limit=10, offset=20)

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result) == 1
        mock_repo.find_by_user.assert_called_once_with(user_id="user_123", limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_memos_empty_result(self):
        """Test listing memos when user has no memos"""
        # Arrange
        mock_repo = Mock()
        mock_repo.find_by_user = AsyncMock(return_value=[])

        use_case = ListMemosUseCase(mock_repo)
        query = ListMemosQuery(user_id="user_123")

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result == []
        mock_repo.find_by_user.assert_called_once()


@pytest.mark.unit
class TestUpdateMemoUseCase:
    """Test cases for UpdateMemoUseCase"""

    @pytest.mark.asyncio
    async def test_update_memo_content(self):
        """Test updating memo content"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Original content",
            user_id="user_123",
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)
        mock_repo.save = AsyncMock()

        use_case = UpdateMemoUseCase(mock_repo)
        command = UpdateMemoCommand(
            memo_id="memo_123",
            user_id="user_123",
            content="Updated content"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is not None
        assert result.content == "Updated content"
        assert result.visibility == "PRIVATE"  # Unchanged
        assert isinstance(result.updated_at, datetime)
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memo_all_fields(self):
        """Test updating all memo fields"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Original content",
            user_id="user_123",
            visibility="PRIVATE",
            tags=["old"]
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)
        mock_repo.save = AsyncMock()

        use_case = UpdateMemoUseCase(mock_repo)
        command = UpdateMemoCommand(
            memo_id="memo_123",
            user_id="user_123",
            content="Updated content",
            visibility="PUBLIC",
            tags=["new", "tags"]
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.content == "Updated content"
        assert result.visibility == "PUBLIC"
        assert result.tags == ["new", "tags"]
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memo_not_found(self):
        """Test updating a non-existent memo"""
        # Arrange
        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=None)

        use_case = UpdateMemoUseCase(mock_repo)
        command = UpdateMemoCommand(
            memo_id="nonexistent",
            user_id="user_123",
            content="Updated content"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is None
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_memo_unauthorized(self):
        """Test updating a memo owned by another user"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Original content",
            user_id="user_456",  # Different user
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)

        use_case = UpdateMemoUseCase(mock_repo)
        command = UpdateMemoCommand(
            memo_id="memo_123",
            user_id="user_123",  # Different user
            content="Updated content"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is None
        mock_repo.save.assert_not_called()


@pytest.mark.unit
class TestDeleteMemoUseCase:
    """Test cases for DeleteMemoUseCase"""

    @pytest.mark.asyncio
    async def test_delete_memo_success(self):
        """Test deleting a memo successfully"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Test content",
            user_id="user_123",
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)
        mock_repo.delete = AsyncMock()

        use_case = DeleteMemoUseCase(mock_repo)
        command = DeleteMemoCommand(
            memo_id="memo_123",
            user_id="user_123"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is True
        mock_repo.find_by_id.assert_called_once_with("memo_123")
        mock_repo.delete.assert_called_once_with("memo_123")

    @pytest.mark.asyncio
    async def test_delete_memo_not_found(self):
        """Test deleting a non-existent memo"""
        # Arrange
        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=None)

        use_case = DeleteMemoUseCase(mock_repo)
        command = DeleteMemoCommand(
            memo_id="nonexistent",
            user_id="user_123"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is False
        mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_memo_unauthorized(self):
        """Test deleting a memo owned by another user"""
        # Arrange
        memo = Memo(
            id="memo_123",
            content="Test content",
            user_id="user_456",  # Different user
            visibility="PRIVATE"
        )

        mock_repo = Mock()
        mock_repo.find_by_id = AsyncMock(return_value=memo)

        use_case = DeleteMemoUseCase(mock_repo)
        command = DeleteMemoCommand(
            memo_id="memo_123",
            user_id="user_123"  # Different user
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is False
        mock_repo.delete.assert_not_called()
