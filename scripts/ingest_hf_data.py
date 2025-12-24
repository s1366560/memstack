import asyncio
import logging

import httpx
from datasets import load_dataset
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
API_URL = "http://localhost:8000/api/v1"
API_KEY = "ms_sk_6b9c69ebc838424f37a4b70c300181d88326cdffbdb7a10622373192d83ce1f0"
PROJECT_ID = "670f6a2a-84e0-41c8-81bd-d33c5d94bdb3"


async def ingest_dataset():
    """Ingest semantic graph data from a Hugging Face dataset."""

    # Using 'clue' dataset, 'csl' subset (Chinese Scientific Literature)
    # It contains abstracts and keywords from scientific papers
    # This is excellent for building a knowledge graph of concepts
    logger.info("Loading dataset 'clue/csl'...")
    dataset = load_dataset("clue", "csl", split="train", streaming=True)

    # Take a subset to avoid overwhelming the system
    # Just 1 items to verify extraction
    items = list(dataset.take(1))

    logger.info(f"Loaded {len(items)} items. Starting ingestion...")

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        success_count = 0

        for item in tqdm(items):
            # Construct a rich text representation
            abstract = item.get("abst", "")
            keywords = item.get("keyword", [])
            label = item.get("label", "")
            corpus_id = item.get("corpus_id", "")

            # Join keywords if it's a list
            if isinstance(keywords, list):
                keywords_str = ", ".join(keywords)
            else:
                keywords_str = str(keywords)

            content = f"Abstract: {abstract}\n"
            content += f"Keywords: {keywords_str}"

            # Create a meaningful name
            # Use the first part of abstract as title since title is missing
            name = abstract[:30] + "..." if len(abstract) > 30 else abstract
            if not name:
                name = "Untitled Paper"

            payload = {
                "content": content,
                "source_type": "document",
                "project_id": PROJECT_ID,
                "name": name,
                "metadata": {
                    "dataset": "clue/csl",
                    "source": "huggingface",
                    "corpus_id": str(corpus_id),
                    "label": str(label),
                    "keywords": keywords,
                },
            }

            try:
                resp = await client.post(f"{API_URL}/episodes/", json=payload, headers=headers)

                if resp.status_code in [200, 201, 202]:
                    success_count += 1
                else:
                    logger.error(f"Failed to ingest item: {resp.status_code} - {resp.text}")

            except Exception as e:
                logger.error(f"Error sending request: {e}")

            # Longer delay to avoid rate limits
            logger.info("Sleeping for 10 seconds to avoid rate limits...")
            await asyncio.sleep(10.0)

    logger.info(f"Ingestion complete. Successfully ingested {success_count}/{len(items)} items.")


if __name__ == "__main__":
    asyncio.run(ingest_dataset())
