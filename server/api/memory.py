"""API routes for memory search."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from server.models.memory import MemoryQuery, MemoryResponse
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/memory', tags=['memory'])


@router.post('/search', response_model=MemoryResponse)
async def search_memory(
    query: MemoryQuery,
    graphiti: GraphitiService = Depends(get_graphiti_service),
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

    Returns:
        Memory search results
    """
    try:
        # Perform search using Graphiti
        results = await graphiti.search(
            query=query.query,
            limit=query.limit,
            tenant_id=query.tenant_id,
        )

        return MemoryResponse(
            results=results,
            total=len(results),
            query=query.query,
        )

    except Exception as e:
        logger.error(f'Memory search failed: {e}')
        raise HTTPException(status_code=500, detail=f'Search failed: {str(e)}')
