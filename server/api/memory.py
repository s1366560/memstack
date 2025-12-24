"""API routes for memory search."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.models.memory import MemoryQuery, MemoryResponse
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/graph")
async def get_graph(
    limit: int = 100,
    since: str | None = None,
    tenant_id: str | None = None,
    project_id: str | None = None,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """Get knowledge graph data for visualization.

    Optional filters:
    - since: ISO datetime string to fetch incremental updates
    - tenant_id: filter by tenant
    - project_id: filter by project
    """
    logger.info(
        f"get_graph called with: limit={limit}, since={since}, tenant_id={tenant_id}, project_id={project_id}, user={api_key.user_id}"
    )
    try:
        parsed_since = None
        if since:
            try:
                from datetime import datetime

                parsed_since = datetime.fromisoformat(since)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        return await graphiti.get_graph_data(
            limit=limit, since=parsed_since, tenant_id=tenant_id, project_id=project_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph retrieval failed: {str(e)}")


@router.post("/search", response_model=MemoryResponse)
async def search_memory(
    query: MemoryQuery,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Search the knowledge graph for relevant memories.

    This endpoint performs semantic search across:
    - Episodes (raw events)
    - Entities (extracted semantic entities)
    - Relations (relationships between entities)

    Args:
        query: Search query parameters
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Memory search results
    """
    try:
        logger.info(f"Memory search by user {api_key.user_id}: {query.query}")

        # Perform search using Graphiti
        parsed_as_of = None
        if query.as_of:
            try:
                from datetime import datetime

                parsed_as_of = datetime.fromisoformat(query.as_of)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid 'as_of' datetime format")

        results = await graphiti.search(
            query=query.query,
            limit=query.limit,
            tenant_id=query.tenant_id,
            project_id=query.project_id,
            user_id=query.user_id,
            as_of=parsed_as_of,
        )

        return MemoryResponse(
            results=results,
            total=len(results),
            query=query.query,
        )

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
