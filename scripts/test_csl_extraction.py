
import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.graphiti_service import get_graphiti_service
from server.models.episode import EpisodeCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    service = await get_graphiti_service()
    await service.initialize()
    
    try:
        # Sample from clue/csl
        content = """
Title: 氧化铁纳米粒子标记神经干细胞的研究
Category: 医药卫生科技
Keywords: 粒子, 铁化合物, 联合, 0.05
Abstract: 目的探讨常见氧化铁纳米粒子几种神经干细胞标记技术的标记效率.材料与方法使用超顺磁性氧化铁纳米粒子(SPIO)和超微超顺磁性氧化铁纳米粒子(USPIO)以25μgFe/ml分别单独标记、与多聚赖氨酸(PLL)及脂质体联合标记神经干细胞,以未标记细胞做对照,采用普鲁士蓝染色评价细胞标记率,并采用4.7TMRIT2WI多回波序列测量T2弛豫率(R2)评价细胞内的铁摄取量,比较各组R2的差异.
"""
        episode_data = EpisodeCreate(
            content=content,
            source_type="document",
            project_id="test-project-chinese-csl",
            name="CSL Test Paper"
        )
        
        logger.info("Adding CSL test episode...")
        episode = await service.add_episode(episode_data)
        logger.info(f"Episode added: {episode.id}")
        
        # Check if entities were created
        query = """
        MATCH (e:Episodic {name: 'CSL Test Paper'})-[:MENTIONS]->(n:Entity)
        RETURN n.name, n.entity_type
        """
        result = await service.client.driver.execute_query(query)
        
        if result.records:
            logger.info(f"Found {len(result.records)} entities linked to the episode:")
            for r in result.records:
                logger.info(f" - {r['n.name']} ({r['n.entity_type']})")
        else:
            logger.warning("No entities found linked to the episode!")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())
