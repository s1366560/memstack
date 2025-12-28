"""Episode management API routes using isolated Graphiti client (Solution 2).

This router is identical to episodes.py but uses get_isolated_graphiti_client
instead of get_graphiti_client for testing Solution 2.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.infrastructure.adapters.primary.web.dependencies import get_current_user, get_isolated_graphiti_client
from src.infrastructure.adapters.secondary.persistence.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/episodes-isolated", tags=["episodes-isolated"])


# --- Schemas (same as episodes.py) ---

class EpisodeCreate(BaseModel):
    name: Optional[str] = None  # Auto-generated if not provided
    content: str
    source_description: Optional[str] = "text"
    episode_type: Optional[str] = "text"
    metadata: Optional[dict] = None
    project_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None


class EpisodeResponse(BaseModel):
    id: str
    name: str
    content: str
    status: str
    created_at: Optional[str] = None
    message: Optional[str] = None


class EpisodeDetail(BaseModel):
    uuid: str
    name: str
    content: str
    source_description: Optional[str] = None
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None


# --- Endpoints (Solution 2: Isolated Client) ---

@router.post("/", response_model=EpisodeResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_episode_isolated(
    episode: EpisodeCreate,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_isolated_graphiti_client)
):
    """
    Create a new episode using isolated Graphiti client (Solution 2).

    SOLUTION 2: Each request gets its own independent Graphiti client instance.
    This ensures complete isolation - no global state mutation possible.

    Trade-offs:
    - Pros: Complete isolation, simpler code (no manual state restoration needed)
    - Cons: Creates new driver connection per request (higher overhead)
    """
    try:
        from uuid import uuid4

        # Auto-generate name if missing
        if not episode.name:
            episode.name = episode.content[:50] + "..."

        # Create episode in Graphiti
        group_id = episode.project_id or "neo4j"  # Use "neo4j" for CE

        # SOLUTION 2: No state restoration needed - client is isolated
        start_time = datetime.utcnow()

        result = await graphiti_client.add_episode(
            group_id=group_id,
            name=episode.name,
            episode_body=episode.content,
            source_description=episode.source_description or "text",
            reference_time=datetime.utcnow(),
        )

        episode_uuid = result.episode.uuid if result.episode else str(uuid4())

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"[Solution 2] Episode created by user {current_user.id}: {episode_uuid} (took {elapsed_ms:.2f}ms)")

        return EpisodeResponse(
            id=episode_uuid,
            name=episode.name,
            content=episode.content,
            status="processing",
            message=f"Episode queued for ingestion (Solution 2: isolated client)",
            created_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"[Solution 2] Failed to create episode: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create episode: {str(e)}")


@router.get("/{episode_name}", response_model=EpisodeDetail)
async def get_episode_isolated(
    episode_name: str,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_isolated_graphiti_client)
):
    """
    Get episode details using isolated client (Solution 2).
    """
    try:
        query = """
        MATCH (e:Episodic {name: $name})
        RETURN properties(e) as props
        """

        result = await graphiti_client.driver.execute_query(query, name=episode_name)

        if not result.records:
            raise HTTPException(status_code=404, detail="Episode not found")

        props = result.records[0]["props"]

        return EpisodeDetail(
            uuid=props.get("uuid", ""),
            name=props.get("name", ""),
            content=props.get("content", ""),
            source_description=props.get("source_description"),
            created_at=props.get("created_at"),
            valid_at=props.get("valid_at"),
            tenant_id=props.get("tenant_id"),
            project_id=props.get("project_id"),
            user_id=props.get("user_id"),
            status=props.get("status", "unknown")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Solution 2] Failed to get episode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_episodes_isolated(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending if True"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_isolated_graphiti_client)
):
    """
    List episodes using isolated client (Solution 2).
    """
    try:
        conditions = []
        if tenant_id:
            conditions.append("e.tenant_id = $tenant_id")
        if project_id:
            conditions.append("e.project_id = $project_id")
        if user_id:
            conditions.append("e.user_id = $user_id")

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count
        count_query = f"MATCH (e:Episodic) {where_clause} RETURN count(e) as total"
        count_result = await graphiti_client.driver.execute_query(
            count_query,
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id
        )
        total = count_result.records[0]["total"] if count_result.records else 0

        # List
        order_clause = "DESC" if sort_desc else "ASC"
        list_query = f"""
        MATCH (e:Episodic)
        {where_clause}
        RETURN properties(e) as props
        ORDER BY e.{sort_by} {order_clause}
        SKIP $offset
        LIMIT $limit
        """

        result = await graphiti_client.driver.execute_query(
            list_query,
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            offset=offset,
            limit=limit
        )

        episodes = []
        for r in result.records:
            props = r["props"]
            episodes.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "content": props.get("content", ""),
                "source_description": props.get("source_description"),
                "created_at": props.get("created_at"),
                "valid_at": props.get("valid_at"),
                "tenant_id": props.get("tenant_id"),
                "project_id": props.get("project_id"),
                "user_id": props.get("user_id"),
                "status": props.get("status", "unknown")
            })

        return {
            "episodes": episodes,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(episodes) < total,
            "solution": "isolated_client"
        }

    except Exception as e:
        logger.error(f"[Solution 2] Failed to list episodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict)
async def health_check_isolated(
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_isolated_graphiti_client)
):
    """
    Health check endpoint for isolated client solution (Solution 2).
    """
    try:
        await graphiti_client.driver.execute_query("RETURN 1 as test")
        return {
            "status": "healthy",
            "solution": "isolated_client",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
