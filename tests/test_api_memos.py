from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from server.auth import get_current_user
from server.database import get_db
from server.db_models import Memo as DBMemo
from server.main import app


@pytest.fixture
def mock_memo_data():
    return {"content": "Test Memo Content", "visibility": "private", "tags": ["test", "memo"]}


from datetime import datetime


@pytest.fixture
def mock_memo_obj(mock_memo_data, test_user):
    return DBMemo(
        id=str(uuid4()),
        user_id=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **mock_memo_data,
    )


@pytest.mark.asyncio
async def test_create_memo(mock_db_session, test_user, mock_memo_data):
    # Setup overrides
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mock refresh to set timestamps
    async def mock_refresh(instance):
        instance.created_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()

    mock_db_session.refresh.side_effect = mock_refresh

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/memos", json=mock_memo_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == mock_memo_data["content"]
    assert data["user_id"] == test_user.id

    # Verify DB interactions
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    assert mock_db_session.refresh.called

    # Clean up
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_list_memos(mock_db_session, test_user, mock_memo_obj):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mock DB result
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_memo_obj]
    mock_db_session.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/memos")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == mock_memo_obj.id

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_memo(mock_db_session, test_user, mock_memo_obj):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mock DB result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_memo_obj
    mock_db_session.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/memos/{mock_memo_obj.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == mock_memo_obj.id

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_memo_not_found(mock_db_session, test_user):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/memos/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_memo(mock_db_session, test_user, mock_memo_obj):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_memo_obj
    mock_db_session.execute.return_value = mock_result

    update_data = {"content": "Updated Content"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch(f"/api/v1/memos/{mock_memo_obj.id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    assert mock_memo_obj.content == "Updated Content"
    assert mock_db_session.commit.called
    assert mock_db_session.refresh.called

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_memo(mock_db_session, test_user, mock_memo_obj):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_memo_obj
    mock_db_session.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete(f"/api/v1/memos/{mock_memo_obj.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert mock_db_session.delete.called
    assert mock_db_session.commit.called

    app.dependency_overrides = {}
