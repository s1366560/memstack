"""Enhanced search API routes with advanced filtering and capabilities."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search-enhanced", tags=["search-enhanced"])


@router.post("/graph-traversal")
async def search_by_graph_traversal(
    start_entity_uuid: str = Body(..., description="Starting entity UUID"),
    max_depth: int = Body(2, ge=1, le=5, description="Maximum traversal depth"),
    relationship_types: Optional[List[str]] = Body(
        None, description="Relationship types to follow"
    ),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Search by traversing the knowledge graph from a starting entity.

    This performs graph traversal to find related entities, episodes, and communities.
    Useful for exploring connections and discovering related content.

    Args:
        start_entity_uuid: Starting entity UUID
        max_depth: Maximum traversal depth (1-3 recommended)
        relationship_types: Optional relationship type filters
        limit: Maximum results to return
        tenant_id: Optional tenant filter

    Returns:
        List of related memory items
    """
    try:
        results = await graphiti.search_by_graph_traversal(
            start_entity_uuid=start_entity_uuid,
            max_depth=max_depth,
            relationship_types=relationship_types,
            limit=limit,
            tenant_id=tenant_id,
        )

        return {
            "results": [r.model_dump() for r in results],
            "total": len(results),
            "search_type": "graph_traversal",
        }
    except Exception as e:
        logger.error(f"Graph traversal search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/community")
async def search_by_community(
    community_uuid: str = Body(..., description="Community UUID"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    include_episodes: bool = Body(True, description="Include episodes in results"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Search within a community for related content.

    This finds all entities and optionally episodes within a specific community.

    Args:
        community_uuid: Community UUID
        limit: Maximum results to return
        include_episodes: Include episodes related to community entities

    Returns:
        List of memory items from the community
    """
    try:
        results = await graphiti.search_by_community(
            community_uuid=community_uuid,
            limit=limit,
            include_episodes=include_episodes,
        )

        return {
            "results": [r.model_dump() for r in results],
            "total": len(results),
            "search_type": "community",
        }
    except Exception as e:
        logger.error(f"Community search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/temporal")
async def search_temporal(
    query: str = Body(..., description="Search query"),
    since: Optional[str] = Body(None, description="Start of time range (ISO format)"),
    until: Optional[str] = Body(None, description="End of time range (ISO format)"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Search within a temporal window.

    Performs semantic search restricted to a specific time range.
    Useful for finding memories from specific periods.

    Args:
        query: Search query
        since: Start of time range (inclusive, ISO format)
        until: End of time range (exclusive, ISO format)
        limit: Maximum results to return
        tenant_id: Optional tenant filter

    Returns:
        List of memory items within the time range
    """
    try:
        parsed_since = None
        parsed_until = None

        if since:
            try:
                parsed_since = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        if until:
            try:
                parsed_until = datetime.fromisoformat(until)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'until' datetime format")

        results = await graphiti.search_temporal(
            query=query,
            since=parsed_since,
            until=parsed_until,
            limit=limit,
            tenant_id=tenant_id,
        )

        return {
            "results": [r.model_dump() for r in results],
            "total": len(results),
            "search_type": "temporal",
            "time_range": {
                "since": since,
                "until": until,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Temporal search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faceted")
async def search_with_facets(
    query: str = Body(..., description="Search query"),
    entity_types: Optional[List[str]] = Body(None, description="Filter by entity types"),
    tags: Optional[List[str]] = Body(None, description="Filter by tags"),
    since: Optional[str] = Body(None, description="Filter by creation date (ISO format)"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    offset: int = Body(0, ge=0, description="Pagination offset"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Search with faceted filtering.

    Performs semantic search with additional filters and returns facet counts
    for UI filtering controls.

    Args:
        query: Search query
        entity_types: Filter by entity types
        tags: Filter by tags
        since: Filter by creation date (ISO format)
        limit: Maximum results to return
        offset: Pagination offset
        tenant_id: Optional tenant filter

    Returns:
        Search results with facet metadata
    """
    try:
        parsed_since = None
        if since:
            try:
                parsed_since = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        results, facets = await graphiti.search_with_facets(
            query=query,
            entity_types=entity_types,
            tags=tags,
            since=parsed_since,
            limit=limit,
            offset=offset,
            tenant_id=tenant_id,
        )

        return {
            "results": [r.model_dump() for r in results],
            "facets": facets,
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "search_type": "faceted",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Faceted search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_search_capabilities(
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get available search capabilities and configuration.

    Returns information about available search types and their parameters.
    """
    return {
        "search_types": {
            "semantic": {
                "description": "Semantic search using embeddings and hybrid retrieval",
                "endpoint": "/api/v1/memory/search",
                "parameters": {
                    "query": "string (required)",
                    "limit": "integer (1-100)",
                    "tenant_id": "string (optional)",
                    "project_id": "string (optional)",
                },
            },
            "graph_traversal": {
                "description": "Search by traversing the knowledge graph",
                "endpoint": "/api/v1/search-enhanced/graph-traversal",
                "parameters": {
                    "start_entity_uuid": "string (required)",
                    "max_depth": "integer (1-5)",
                    "relationship_types": "array of strings (optional)",
                    "limit": "integer (1-200)",
                },
            },
            "community": {
                "description": "Search within a specific community",
                "endpoint": "/api/v1/search-enhanced/community",
                "parameters": {
                    "community_uuid": "string (required)",
                    "limit": "integer (1-200)",
                    "include_episodes": "boolean",
                },
            },
            "temporal": {
                "description": "Search within a time range",
                "endpoint": "/api/v1/search-enhanced/temporal",
                "parameters": {
                    "query": "string (required)",
                    "since": "ISO datetime string (optional)",
                    "until": "ISO datetime string (optional)",
                    "limit": "integer (1-200)",
                },
            },
            "faceted": {
                "description": "Search with faceted filtering",
                "endpoint": "/api/v1/search-enhanced/faceted",
                "parameters": {
                    "query": "string (required)",
                    "entity_types": "array of strings (optional)",
                    "tags": "array of strings (optional)",
                    "since": "ISO datetime string (optional)",
                    "limit": "integer (1-200)",
                    "offset": "integer (0+)",
                },
            },
        },
        "filters": {
            "entity_types": [
                "Person",
                "Organization",
                "Product",
                "Location",
                "Event",
                "Concept",
                "Custom",
            ],
            "relationship_types": [
                "RELATES_TO",
                "MENTIONS",
                "PART_OF",
                "CONTAINS",
                "BELONGS_TO",
                "OWNS",
                "LOCATED_AT",
            ],
        },
    }
