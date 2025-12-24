from datetime import datetime
from uuid import uuid4

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.auth import get_current_user, verify_api_key_dependency
from server.config import get_settings
from server.database import get_db
from server.db_models import APIKey, User
from server.main import app
from server.services.graphiti_service import graphiti_service


@pytest.fixture
async def integration_db_override():
    settings = get_settings()
    engine = create_async_engine(settings.postgres_url)
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with TestingSessionLocal() as session:
            yield session

    yield _get_db

    await engine.dispose()


# Mock authentication
async def mock_get_current_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == "test@example.com"))
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
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def mock_verify_api_key():
    return APIKey(user_id="user_test_123", permissions=["read", "write"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_flow(integration_db_override):
    print("🚀 Starting Integration Test: Memory Flow")

    # Initialize Graphiti Service
    settings = get_settings()
    try:
        await graphiti_service.initialize(provider=settings.llm_provider)
        print("✅ Graphiti Service Initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Graphiti Service: {e}")
        # Continue anyway

    # Override dependency
    app.dependency_overrides[get_db] = integration_db_override
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[verify_api_key_dependency] = mock_verify_api_key

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as AC:
            # 1. Get/Create Tenant
            print("\n1. Getting Tenant...")
            await AC.get("/api/v1/users/me")

            tenant_response = await AC.post(
                "/api/v1/tenants/",
                json={
                    "name": "Memory Test Tenant",
                    "description": "Tenant for memory tests",
                    "plan": "free",
                },
            )

            tenant_id = ""
            if tenant_response.status_code == 201:
                tenant_id = tenant_response.json()["id"]
            elif tenant_response.status_code == 400:
                # List tenants
                list_response = await AC.get("/api/v1/tenants/")
                if list_response.json()["tenants"]:
                    tenant_id = list_response.json()["tenants"][0]["id"]
                else:
                    pytest.fail("❌ No tenant available")

            print(f"✅ Tenant ID: {tenant_id}")

            # 2. Create Project
            print("\n2. Creating Project...")
            project_data = {
                "name": f"Memory Test Project {uuid4().hex[:6]}",
                "description": "Integration Test Project for Memories",
                "tenant_id": tenant_id,
                "memory_rules": {
                    "max_episodes": 1000,
                    "retention_days": 30,
                    "auto_refresh": True,
                    "refresh_interval": 24,
                },
                "graph_config": {
                    "layout_algorithm": "force-directed",
                    "node_size": 20,
                    "edge_width": 2,
                    "colors": {},
                    "animations": True,
                    "max_nodes": 5000,
                    "max_edges": 10000,
                    "similarity_threshold": 0.7,
                    "community_detection": True,
                },
                "is_public": False,
            }

            response = await AC.post("/api/v1/projects/", json=project_data)
            project_id = ""
            if response.status_code == 201:
                project_id = response.json()["id"]
                print(f"✅ Project Created: {project_id}")
            elif response.status_code == 400 and "maximum number of projects" in response.text:
                print("⚠️ Tenant project limit reached, using existing project...")
                list_response = await AC.get(f"/api/v1/projects/?tenant_id={tenant_id}")
                if list_response.status_code == 200 and list_response.json()["projects"]:
                    project_id = list_response.json()["projects"][0]["id"]
                    print(f"✅ Using Existing Project: {project_id}")
                else:
                    pytest.fail("❌ Failed to list projects or no projects found")
            else:
                pytest.fail(f"❌ Create Project failed: {response.status_code} - {response.text}")

            # 3. Create Memory
            print("\n3. Creating Memory...")
            memory_data = {
                "title": "Test Memory",
                "content": "This is a test memory content.",
                "content_type": "text",
                "project_id": project_id,
                "tags": ["test", "integration"],
                "entities": [
                    {
                        "id": "entity1",
                        "name": "Test Entity",
                        "type": "concept",
                        "properties": {"importance": "high"},
                        "confidence": 0.95,
                    }
                ],
                "relationships": [],
                "collaborators": [],
                "is_public": False,
                "metadata": {"source": "test_script"},
            }

            response = await AC.post("/api/v1/memories/", json=memory_data)

            if response.status_code == 201:
                memory = response.json()
                print(f"✅ Memory created successfully: {memory['id']}")
                print(f"   Entities: {memory['entities']}")
            else:
                pytest.fail(f"❌ Create Memory failed: {response.status_code} - {response.text}")

            memory_id = memory["id"]

            # 4. List Memories
            print("\n4. Listing Memories...")
            response = await AC.get(f"/api/v1/memories/?project_id={project_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Listed {data['total']} memories")
                assert data["total"] >= 1
                # Check if our memory is in the list
                found = False
                for m in data["memories"]:
                    if m["id"] == memory_id:
                        found = True
                        break
                assert found, f"Created memory {memory_id} not found in list"
            else:
                pytest.fail(f"❌ List Memories failed: {response.status_code} - {response.text}")

            # 5. Get Memory
            print("\n5. Getting Memory...")
            response = await AC.get(f"/api/v1/memories/{memory_id}")
            assert response.status_code == 200

        print("\n✅ All Memory Integration Tests Passed!")

    finally:
        app.dependency_overrides = {}
        # Cleanup
        try:
            await graphiti_service.close()
            print("✅ Graphiti Service Closed")
        except Exception as e:
            print(f"❌ Failed to close Graphiti Service: {e}")
