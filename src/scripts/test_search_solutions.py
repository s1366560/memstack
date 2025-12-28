"""Quick test of both search solutions."""
import asyncio
import httpx

async def main():
    # Get auth token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/token",
            data={"username": "admin@memstack.ai", "password": "adminpassword"}
        )
        token = response.json()["access_token"]

        # Test Solution 1
        response1 = await client.post(
            "http://localhost:8000/api/v1/search-enhanced/advanced",
            json={"query": "张三", "limit": 10},
            headers={"Authorization": f"Bearer {token}"}
        )
        data1 = response1.json()

        # Test Solution 2
        response2 = await client.post(
            "http://localhost:8000/api/v1/search-isolated/advanced",
            json={"query": "张三", "limit": 10},
            headers={"Authorization": f"Bearer {token}"}
        )
        data2 = response2.json()

        print("Solution 1 (Shared Client):")
        print(f"  Total results: {data1.get('total', 0)}")
        if data1.get('results'):
            print(f"  First result: {data1['results'][0].get('name', 'N/A')}")

        print("\nSolution 2 (Isolated Client):")
        print(f"  Total results: {data2.get('total', 0)}")
        if data2.get('results'):
            print(f"  First result: {data2['results'][0].get('name', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
