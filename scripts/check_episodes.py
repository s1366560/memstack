import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.graphiti_service import get_graphiti_service


async def main():
    service = await get_graphiti_service()
    await service.initialize()

    try:
        print("Checking episodes...")
        query = """
        MATCH (e:Episodic)
        RETURN count(e) as count
        """
        result = await service.client.driver.execute_query(query)
        count = result.records[0]["count"]
        print(f"Total Episodes: {count}")

        query_sample = """
        MATCH (e:Episodic)
        WHERE e.project_id = '670f6a2a-84e0-41c8-81bd-d33c5d94bdb3'
        RETURN e.name, e.content
        ORDER BY e.created_at DESC
        LIMIT 5
        """
        result_sample = await service.client.driver.execute_query(query_sample)
        print("Recent Episodes for Project:")
        for r in result_sample.records:
            print(f" - {r['e.name']}")
            print(f"   Content Preview: {r['e.content'][:100]}...")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
