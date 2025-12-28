"""Enhanced search API routes using isolated Graphiti client (Solution 2).

This router is identical to enhanced_search.py but uses get_isolated_graphiti_client
for testing Solution 2.
"""

import logging
from datetime import datetime
from typing import List, Optional

import graphiti_core.search.search_config_recipes as recipes
from fastapi import APIRouter, Body, Depends, HTTPException

from src.infrastructure.adapters.primary.web.dependencies import get_current_user, get_isolated_graphiti_client
from src.infrastructure.adapters.secondary.persistence.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search-isolated", tags=["search-isolated"])


# --- Endpoints (Solution 2: Isolated Client) ---

@router.post("/advanced")
async def search_advanced_isolated(
    query: str = Body(..., description="Search query"),
    strategy: str = Body("COMBINED_HYBRID_SEARCH_RRF", description="Search strategy recipe name"),
    focal_node_uuid: Optional[str] = Body(None, description="Focal node UUID for Node Distance Reranking"),
    reranker: Optional[str] = Body(None, description="Reranker client (openai, gemini, bge)"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    project_id: Optional[str] = Body(None, description="Project filter"),
    since: Optional[str] = Body(None, description="Filter by creation date (ISO format)"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_isolated_graphiti_client)
):
    """
    Perform advanced search using isolated Graphiti client (Solution 2).

    SOLUTION 2: Each request gets its own independent Graphiti client instance.
    """
    logger.info(f"[Solution 2] search_advanced called: query='{query}', project_id='{project_id}'")
    start_time = datetime.utcnow()

    try:
        # Get recipe from strategy name
        search_config = getattr(recipes, strategy, None)
        if not search_config:
            logger.warning(f"Unknown strategy {strategy}, falling back to COMBINED_HYBRID_SEARCH_RRF")
            search_config = recipes.COMBINED_HYBRID_SEARCH_RRF

        parsed_since = None
        if since:
            try:
                parsed_since = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        # Prepare search parameters
        group_id = project_id if project_id else None
        group_ids = [group_id] if group_id else None

        # Perform search
        results = await graphiti_client.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
        )

        # Convert results to dict format
        formatted_results = []
        if hasattr(results, "episodes") and results.episodes:
            for ep in results.episodes:
                formatted_results.append({
                    "uuid": ep.uuid,
                    "name": getattr(ep, "name", ""),
                    "content": ep.content,
                    "type": "episode",
                    "score": getattr(ep, "score", 0.0),
                    "created_at": getattr(ep, "created_at", None),
                    "metadata": {
                        "source": getattr(ep, "source", ""),
                        "source_description": getattr(ep, "source_description", ""),
                    }
                })

        if hasattr(results, "nodes") and results.nodes:
            for node in results.nodes:
                formatted_results.append({
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": getattr(node, "summary", ""),
                    "type": "entity",
                    "entity_type": getattr(node, "entity_type", "Unknown"),
                    "score": getattr(node, "score", 0.0),
                    "created_at": getattr(node, "created_at", None),
                    "metadata": {}
                })

        # Sort by score and limit
        formatted_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        formatted_results = formatted_results[:limit]

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"[Solution 2] Search completed: {len(formatted_results)} results in {elapsed_ms:.2f}ms")

        return {
            "results": formatted_results,
            "total": len(formatted_results),
            "search_type": "advanced",
            "strategy": strategy,
            "solution": "isolated_client",
            "elapsed_ms": elapsed_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Solution 2] Advanced search failed: {e}")
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
