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
        print("Finding episodes without entities...")
        # Find episodes that don't mention any entity
        query = """
        MATCH (e:Episodic)
        WHERE NOT (e)-[:MENTIONS]->(:Entity)
        AND e.source_description = 'document'
        RETURN e.name, e.uuid
        """
        result = await service.client.driver.execute_query(query)
        print(f"Found {len(result.records)} empty episodes.")

        for r in result.records:
            print(f"Deleting {r['e.name']}...")
            await service.delete_episode(r["e.name"])

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
