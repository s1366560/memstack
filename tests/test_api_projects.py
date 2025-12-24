from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from server.auth import verify_api_key_dependency
from server.database import get_db
from server.db_models import APIKey
from server.main import app


@pytest.fixture
def mock_api_key_dependency(test_user):
    return APIKey(
        id=str(uuid4()),
        key_hash="hash",
        name="test-key",
        user_id=test_user.id,
        permissions=["read", "write"],
    )


@pytest.mark.asyncio
async def test_create_project_invalid_data(mock_api_key_dependency, mock_db_session, test_user):
    # Mock user retrieval for verify_api_key_dependency -> get_current_user
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_db_session.execute.return_value = mock_result

    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_db] = lambda: mock_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing required fields
        response = await ac.post("/api/v1/projects/", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    app.dependency_overrides = {}
