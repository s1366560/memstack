
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
        print("Checking entities...")
        query = """
        MATCH (e:Entity)
        RETURN count(e) as count
        """
        result = await service.client.driver.execute_query(query)
        count = result.records[0]["count"]
        print(f"Total Entities: {count}")
        
        if count > 0:
            query_sample = """
            MATCH (e:Entity)
            RETURN e.name, e.entity_type, e.project_id
            LIMIT 10
            """
            result_sample = await service.client.driver.execute_query(query_sample)
            print("Sample Entities:")
            for r in result_sample.records:
                print(f" - {r['e.name']} ({r['e.entity_type']}) Project: {r['e.project_id']}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())
