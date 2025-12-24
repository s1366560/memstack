"""API routes for episodes."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.models.episode import EpisodeCreate, EpisodeResponse
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.post("/", response_model=EpisodeResponse, status_code=202)
async def create_episode(
    episode: EpisodeCreate,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Create a new episode and ingest it into the knowledge graph.

    The episode will be processed asynchronously:
    1. Entity extraction
    2. Relationship identification
    3. Community detection and updates

    Args:
        episode: Episode data to create
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Episode response with ID and status
    """
    try:
        # Auto-generate title if missing
        if not episode.name:
            try:
                llm_client = graphiti.client.llm_client
                prompt = f"""
                Generate a concise and descriptive title (max 10 words) for the following text.
                The title must be plain text, no markdown, no hash symbols, no newlines.
                
                Text:
                {episode.content[:1000]}...
                
                Output ONLY the title. Do not use quotes.
                """
                response = await llm_client.generate_response(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Handle response whether it's a dict or object
                if isinstance(response, dict):
                    content = response.get("content", "")
                else:
                    content = getattr(response, "content", str(response))
                    
                episode.name = content.strip().strip('"').strip("'")
            except Exception as e:
                logger.warning(f"Failed to auto-generate title: {e}")
                # Fallback to truncated content
                episode.name = episode.content[:50] + "..."

        # Add episode to Graphiti (this triggers async processing via QueueService)
        created_episode = await graphiti.add_episode(episode)

        logger.info(f"Episode created by user {api_key.user_id}: {created_episode.id}")

        return EpisodeResponse(
            id=created_episode.id,
            status="processing",
            message="Episode queued for ingestion",
            created_at=created_episode.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create episode: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create episode: {str(e)}")


@router.get("/health", response_model=dict)
async def health_check(graphiti: GraphitiService = Depends(get_graphiti_service)):
    """
    Health check endpoint for episode service.

    Returns:
        Health status
    """
    is_healthy = await graphiti.health_check()

    if not is_healthy:
        raise HTTPException(status_code=503, detail="Service unhealthy")

    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
