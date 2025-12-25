import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from server.auth import create_user
from server.config import get_settings
from server.database import get_db
from server.db_models import User
from server.main import app


@pytest.fixture
async def integration_db_override():
    settings = get_settings()
    # Create a fresh engine for this test function to ensure clean loop binding
    engine = create_async_engine(settings.postgres_url)
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with TestingSessionLocal() as session:
            yield session

    yield _get_db

    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_flow(integration_db_override):
    # Override get_db for the app
    app.dependency_overrides[get_db] = integration_db_override

    # Ensure admin user exists using the override
    async for session in integration_db_override():
        # Ensure admin user is fresh
        result = await session.execute(select(User).where(User.email == "admin@memstack.ai"))
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()

        user = await create_user(
            session,
            email="admin@memstack.ai",
            name="Admin User",
            password="admin123",
        )
        break  # Only need one session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Login (POST /auth/token)
        print("\n1. Testing Login (POST /auth/token)...")
        login_data = {"username": "admin@memstack.ai", "password": "admin123"}

        response = await client.post("/api/v1/auth/token", data=login_data)

        if response.status_code != 200:
            pytest.fail(f"❌ Login failed: {response.status_code} - {response.text}")

        token_data = response.json()
        access_token = token_data.get("access_token")
        token_type = token_data.get("token_type")

        assert access_token is not None

        print(f"✅ Login successful! Token type: {token_type}")

        # 2. Test Get Current User (GET /auth/me)
        print("\n2. Testing Get User (GET /auth/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/v1/users/me", headers=headers)

        if response.status_code != 200:
            pytest.fail(f"❌ Get User failed: {response.status_code} - {response.text}")

        user_data = response.json()
        print("✅ Get User successful!")

        assert user_data.get("email") == "admin@memstack.ai"

    app.dependency_overrides = {}
