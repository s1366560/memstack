import asyncio
import sys
from datetime import datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from server.auth import get_current_user
from server.config import get_settings
from server.database import get_db
from server.db_models import User
from server.main import app
from server.services.graphiti_service import graphiti_service


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


async def main():
    print("🚀 Starting Integration Test: Memory Flow")

    # Initialize Graphiti Service
    settings = get_settings()
    try:
        await graphiti_service.initialize(provider=settings.llm_provider)
        print("✅ Graphiti Service Initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Graphiti Service: {e}")
        # Continue anyway, as some tests might not need it, or we want to see failure

    # Override dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user

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
                    print("❌ No tenant available")
                    sys.exit(1)

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
                    print("❌ Failed to list projects or no projects found")
                    sys.exit(1)
            else:
                print(f"❌ Create Project failed: {response.status_code} - {response.text}")
                sys.exit(1)

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
                print(f"❌ Create Memory failed: {response.status_code} - {response.text}")
                sys.exit(1)

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
                print(f"❌ List Memories failed: {response.status_code} - {response.text}")
                sys.exit(1)

        print("\n✅ All Memory Integration Tests Passed!")

    finally:
        # Cleanup
        try:
            await graphiti_service.close()
            print("✅ Graphiti Service Closed")
        except Exception as e:
            print(f"❌ Failed to close Graphiti Service: {e}")


if __name__ == "__main__":
    asyncio.run(main())
