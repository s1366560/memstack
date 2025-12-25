"""Enhanced Episode management API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/episodes-enhanced", tags=["episodes-enhanced"])


@router.get("/{episode_name}")
async def get_episode(
    episode_name: str,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get episode details by name.

    Args:
        episode_name: Episode name
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Episode details
    """
    try:
        episode = await graphiti.get_episode(episode_name)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        return episode
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get episode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_episodes(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending if True"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    List episodes with filtering and pagination.

    Args:
        tenant_id: Optional tenant filter
        project_id: Optional project filter
        user_id: Optional user filter
        limit: Maximum items to return
        offset: Pagination offset
        sort_by: Sort field
        sort_desc: Sort descending if True
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Paginated list of episodes
    """
    try:
        result = await graphiti.list_episodes(
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

        return {
            "episodes": result.items,
            "total": result.total,
            "limit": result.limit,
            "offset": result.offset,
            "has_more": result.has_more,
        }
    except Exception as e:
        logger.error(f"Failed to list episodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{episode_name}")
async def delete_episode(
    episode_name: str,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Delete an episode and its relationships.

    Warning: This will permanently delete the episode and all
    associated relationships. Entities will be preserved.

    Args:
        episode_name: Episode name
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Deletion status
    """
    try:
        deleted = await graphiti.delete_episode(episode_name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Episode not found")
        return {"status": "success", "message": f"Episode '{episode_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete episode: {e}")
        raise HTTPException(status_code=500, detail=str(e))
