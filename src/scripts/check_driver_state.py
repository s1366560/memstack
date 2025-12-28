"""Debug script to check driver state."""
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/api/v1/auth/token',
            data={'username': 'admin@memstack.ai', 'password': 'adminpassword'}
        )
        token = response.json()['access_token']

        # Test search first
        print("1. Initial search (no episodes created yet):")
        r1 = await client.post(
            'http://localhost:8000/api/v1/search-enhanced/advanced',
            json={'query': '张三', 'limit': 10},
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"   Solution 1: {r1.json().get('total', 0)} results")

        # Create an episode
        print("\n2. Creating episode...")
        r2 = await client.post(
            'http://localhost:8000/api/v1/episodes/',
            json={
                'name': 'Test Episode After Search',
                'content': 'This test episode is about 张三.',
                'project_id': 'neo4j'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"   Episode created: {r2.json().get('status', 'unknown')}")

        # Wait a bit for processing
        print("\n3. Waiting 3 seconds for episode processing...")
        await asyncio.sleep(3)

        # Test search again
        print("\n4. Search after episode creation:")
        r3 = await client.post(
            'http://localhost:8000/api/v1/search-enhanced/advanced',
            json={'query': '张三', 'limit': 10},
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"   Solution 1: {r3.json().get('total', 0)} results")

        # Test memory/search for comparison
        r4 = await client.post(
            'http://localhost:8000/api/v1/memory/search',
            json={'query': '张三', 'limit': 10},
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"   memory/search: {r4.json().get('total', 0)} results")

        # Test isolated client
        r5 = await client.post(
            'http://localhost:8000/api/v1/search-isolated/advanced',
            json={'query': '张三', 'limit': 10},
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"   Solution 2: {r5.json().get('total', 0)} results")

asyncio.run(main())
