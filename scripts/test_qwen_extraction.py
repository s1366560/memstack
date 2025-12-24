import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set env vars for Qwen
os.environ["DASHSCOPE_API_KEY"] = "sk-41ef900edb31423e8a43d4bc6a89acfa"
os.environ["QWEN_MODEL"] = "qwen-plus"
os.environ["QWEN_SMALL_MODEL"] = "qwen-turbo"
os.environ["QWEN_EMBEDDING_MODEL"] = "text-embedding-v3"
os.environ["QWEN_BASE_URL"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

from server.models.episode import EpisodeCreate
from server.services.graphiti_service import get_graphiti_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    service = await get_graphiti_service()
    # Explicitly use qwen
    await service.initialize(provider="qwen")

    # Clean up DB to avoid vector dimension mismatch
    logger.info("Cleaning up database...")
    await service.client.driver.execute_query("MATCH (n) DETACH DELETE n")

    try:
        # Chinese test (CSL style)
        content = "计算机科学是研究计算机及其周围各种现象和规律的科学，亦即研究计算机系统结构、程序系统（即软件）、人工智能以及计算本身的性质和问题的学科。"
        episode_data = EpisodeCreate(
            content=content,
            source_type="text",
            project_id="test-project-qwen-chinese",
            name="Qwen Chinese Test",
        )

        logger.info("Adding Chinese test episode with Qwen...")
        episode = await service.add_episode(episode_data)
        logger.info(f"Episode added: {episode.id}")

        # Check if entities were created
        query = """
        MATCH (e:Episodic {name: 'Qwen Chinese Test'})-[:MENTIONS]->(n:Entity)
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
