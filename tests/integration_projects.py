import asyncio
import sys
from datetime import datetime

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from server.auth import get_current_user
from server.database import get_db
from server.db_models import User
from server.main import app


# Mock authentication
async def mock_get_current_user():
    async for session in get_db():
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()
        if not user:
            # Create test user if not exists
            user = User(
                id="user_test_123",
                email="test@example.com",
                name="Test User",
                role="user",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_test_tenant(client, user):
    # Try to list tenants first
    response = await client.get("/api/v1/tenants/")
    if response.status_code == 200:
        data = response.json()
        if data["tenants"]:
            return data["tenants"][0]

    # Create tenant if not exists
    response = await client.post(
        "/api/v1/tenants/",
        json={
            "name": "Test Tenant For Project",
            "description": "Integration Test Tenant",
            "plan": "free",
        },
    )
    if response.status_code == 201:
        return response.json()
    return None


async def main():
    print("🚀 Starting Integration Test: Project Flow")

    # Override dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as AC:
        # 1. Get/Create Tenant
        print("\n1. Getting Tenant...")

        # Override get_current_user to return our mock user directly
        # The auth system uses verify_api_key_dependency which we can also override
        # But since we are mocking get_current_user, we bypass the key check

        # However, to be more realistic, let's inject a fake token if needed,
        # but since we override the dependency, the header is not strictly required
        # UNLESS verify_api_key_dependency is used directly somewhere else.

        # Let's see if we need to set headers for the client
        # AC.headers = {"Authorization": "Bearer vpm_sk_mock_key"}

        # Call an endpoint to trigger user creation logic in our mock
        await AC.get("/api/v1/users/me")

        # Now get tenant
        # We need to simulate the auth flow or just rely on the override
        # The override returns a user object directly

        # But we need a tenant ID to create a project
        # Let's use the API to get/create one

        tenant_response = await AC.post(
            "/api/v1/tenants/",
            json={
                "name": "Project Test Tenant",
                "description": "Tenant for project tests",
                "plan": "free",
            },
        )

        tenant_id = ""
        if tenant_response.status_code == 201:
            tenant_id = tenant_response.json()["id"]
            print(f"✅ Created Tenant: {tenant_id}")
        elif (
            tenant_response.status_code == 400
            and "User already owns a tenant" in tenant_response.text
        ):
            # List tenants
            list_response = await AC.get("/api/v1/tenants/")
            tenant_id = list_response.json()["tenants"][0]["id"]
            print(f"✅ Using existing Tenant: {tenant_id}")
        else:
            print(
                f"❌ Failed to get tenant: {tenant_response.status_code} - {tenant_response.text}"
            )
            sys.exit(1)

        # 2. Create Project with complex config
        print("\n2. Creating Project with Memory Rules Config...")
        project_data = {
            "name": "Test Project",
            "description": "Integration Test Project",
            "tenant_id": tenant_id,
            "memory_rules": {
                "max_episodes": 1000,
                "retention_days": 30,
                "auto_refresh": True,
                "refresh_interval": 24,
            },
            "graph_config": {
                "max_nodes": 5000,
                "max_edges": 10000,
                "similarity_threshold": 0.7,
                "community_detection": True,
            },
            "is_public": False,
        }

        response = await AC.post("/api/v1/projects/", json=project_data)

        if response.status_code == 201:
            project = response.json()
            print(f"✅ Project created successfully: {project['id']}")
            print(f"   Memory Rules: {project['memory_rules']}")
            print(f"   Graph Config: {project['graph_config']}")

            # Verify structure
            assert isinstance(project["memory_rules"], dict)
            assert project["memory_rules"]["max_episodes"] == 1000
            assert project["graph_config"]["community_detection"] is True

        else:
            print(f"❌ Create Project failed: {response.status_code} - {response.text}")
            sys.exit(1)

    print("\n✅ All Project Integration Tests Passed!")


if __name__ == "__main__":
    asyncio.run(main())
