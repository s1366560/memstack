"""Enhanced search API routes with advanced filtering and capabilities."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client
from src.infrastructure.adapters.secondary.persistence.models import User

# Use Cases & DI Container
from src.configuration.di_container import DIContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search-enhanced", tags=["search-enhanced"])


# --- Endpoints ---

@router.post("/advanced")
async def search_advanced(
    query: str = Body(..., description="Search query"),
    strategy: str = Body("COMBINED_HYBRID_SEARCH_RRF", description="Search strategy recipe name"),
    focal_node_uuid: Optional[str] = Body(None, description="Focal node UUID for Node Distance Reranking"),
    reranker: Optional[str] = Body(None, description="Reranker client (openai, gemini, bge)"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    project_id: Optional[str] = Body(None, description="Project filter"),
    since: Optional[str] = Body(None, description="Filter by creation date (ISO format)"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Perform advanced search with configurable strategy and reranking.
    """
    logger.info(f"search_advanced called: query='{query}', project_id='{project_id}'")
    try:
        # Import recipes inside function (same as graphiti.py to avoid state issues)
        import graphiti_core.search.search_config_recipes as recipes

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

        # Prepare search parameters (same as /memory/search)
        group_id = project_id if project_id else None
        group_ids = [group_id] if group_id else None

        # Perform search (EXACT same as /memory/search)
        results = await graphiti_client.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
        )

        # Convert results to dict format with enriched metadata for frontend compatibility
        formatted_results = []
        if hasattr(results, "episodes") and results.episodes:
            for ep in results.episodes:
                # Extract tags if available in metadata, otherwise empty list
                tags = []
                if hasattr(ep, "metadata") and isinstance(ep.metadata, dict):
                    tags = ep.metadata.get("tags", [])
                
                # Determine a better name for the episode
                ep_name = getattr(ep, "name", "")
                ep_source = getattr(ep, "source", "")
                if not ep_name:
                    if ep_source:
                        ep_name = ep_source.split("/")[-1]  # Use filename if available
                    else:
                        # Truncate content for name if no other info
                        content_preview = ep.content[:50].replace("\n", " ")
                        ep_name = f"{content_preview}..." if len(ep.content) > 50 else content_preview

                formatted_results.append({
                    "content": ep.content,
                    "score": getattr(ep, "score", 0.0),
                    "source": getattr(ep, "source", "unknown"),
                    "metadata": {
                        "uuid": ep.uuid,
                        "name": ep_name,
                        "type": "Episode",  # Capitalized for better display
                        "created_at": getattr(ep, "created_at", None),
                        "source_description": getattr(ep, "source_description", ""),
                        "tags": tags,
                        # Preserve original metadata fields
                        **(ep.metadata if hasattr(ep, "metadata") and isinstance(ep.metadata, dict) else {})
                    }
                })

        if hasattr(results, "nodes") and results.nodes:
            for node in results.nodes:
                # Use labels as tags for nodes
                labels = getattr(node, "labels", [])
                tags = labels
                
                # Extract specific entity type from labels (exclude 'Entity' and 'Node')
                entity_type = "Entity"
                ignored_labels = {"Entity", "Node", "BaseEntity"}
                specific_labels = [l for l in labels if l not in ignored_labels]
                if specific_labels:
                    entity_type = specific_labels[0]

                formatted_results.append({
                    "content": getattr(node, "summary", "") or getattr(node, "name", "No content"),
                    "score": getattr(node, "score", 0.0),
                    "source": "Knowledge Graph",
                    "metadata": {
                        "uuid": node.uuid,
                        "name": node.name,
                        "type": entity_type,  # Use specific type (e.g. Person, Organization)
                        "entity_type": entity_type,
                        "created_at": getattr(node, "created_at", None),
                        "tags": tags,
                        # Preserve attributes if available
                        **(getattr(node, "attributes", {}) if hasattr(node, "attributes") else {})
                    }
                })

        # Sort by score and limit (same as /memory/search)
        formatted_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        formatted_results = formatted_results[:limit]

        return {
            "results": formatted_results,
            "total": len(formatted_results),
            "search_type": "advanced",
            "strategy": strategy,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph-traversal")
async def search_by_graph_traversal(
    start_entity_uuid: str = Body(..., description="Starting entity UUID"),
    max_depth: int = Body(2, ge=1, le=5, description="Maximum traversal depth"),
    relationship_types: Optional[List[str]] = Body(None, description="Relationship types to follow"),
    limit: int = Body(50, ge=1, le=200, description="Maximum results"),
    tenant_id: Optional[str] = Body(None, description="Tenant filter"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Search by traversing the knowledge graph from a starting entity.

    This performs graph traversal to find related entities, episodes, and communities.
    Useful for exploring connections and discovering related content.
    """
    try:
        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"AND type(r) IN [{', '.join([f'\"{t}\"' for t in relationship_types])}]"

        query = f"""
        MATCH path = (start:Entity {{uuid: $uuid}})-[*1..{max_depth}]-(related)
        WHERE ('Entity' IN labels(related) OR 'Episodic' IN labels(related) OR 'Community' IN labels(related))
        {rel_filter}
        RETURN DISTINCT related, properties(related) as props, labels(related) as labels
        LIMIT $limit
        """

        result = await graphiti_client.driver.execute_query(
            query,
            uuid=start_entity_uuid,
            limit=limit
        )

        items = []
        for r in result.records:
            props = r["props"]
            labels = r["labels"]
            label = labels[0] if labels else "Unknown"

            items.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "type": label,
                "summary": props.get("summary", ""),
                "content": props.get("content", ""),
                "created_at": props.get("created_at")
            })

        return {
            "results": items,
            "total": len(items),
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
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Search within a community for related content.

    This finds all entities and optionally episodes within a specific community.
    """
    try:
        # Get entities in community
        entity_query = """
        MATCH (c:Community {uuid: $uuid})
        MATCH (e:Entity)-[:BELONGS_TO]->(c)
        RETURN properties(e) as props, 'Entity' as type
        """

        result = await graphiti_client.driver.execute_query(entity_query, uuid=community_uuid)

        items = []
        for r in result.records:
            props = r["props"]
            items.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "type": "entity",
                "summary": props.get("summary", ""),
                "created_at": props.get("created_at")
            })

        # Optionally include episodes
        if include_episodes:
            episode_query = """
            MATCH (c:Community {uuid: $uuid})
            MATCH (e:Entity)-[:BELONGS_TO]->(c)
            MATCH (ep:Episodic)-[:MENTIONS]->(e)
            RETURN DISTINCT properties(ep) as props, 'Episodic' as type
            LIMIT $limit
            """

            ep_result = await graphiti_client.driver.execute_query(
                episode_query,
                uuid=community_uuid,
                limit=limit
            )

            for r in ep_result.records:
                props = r["props"]
                items.append({
                    "uuid": props.get("uuid", ""),
                    "name": props.get("name", ""),
                    "type": "episode",
                    "content": props.get("content", ""),
                    "created_at": props.get("created_at")
                })

        return {
            "results": items[:limit],
            "total": len(items),
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
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Search within a temporal window.

    Performs semantic search restricted to a specific time range.
    Useful for finding memories from specific periods.
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

        # Build temporal filter
        conditions = []
        params = {"query": query, "limit": limit}

        if parsed_since:
            conditions.append("e.created_at >= datetime($since)")
            params["since"] = parsed_since.isoformat()

        if parsed_until:
            conditions.append("e.created_at <= datetime($until)")
            params["until"] = parsed_until.isoformat()

        if tenant_id:
            conditions.append("e.tenant_id = $tenant_id")
            params["tenant_id"] = tenant_id

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        search_query = f"""
        MATCH (e:Episodic)
        {where_clause}
        RETURN properties(e) as props, 'episode' as type
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        result = await graphiti_client.driver.execute_query(search_query, **params)

        items = []
        for r in result.records:
            props = r["props"]
            items.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "type": "episode",
                "content": props.get("content", ""),
                "created_at": props.get("created_at")
            })

        return {
            "results": items,
            "total": len(items),
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
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Search with faceted filtering.

    Performs semantic search with additional filters and returns facet counts
    for UI filtering controls.
    """
    try:
        parsed_since = None
        if since:
            try:
                parsed_since = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        # Build filters
        conditions = []
        params = {"limit": limit, "offset": offset}

        if entity_types:
            conditions.append("e.entity_type IN $entity_types")
            params["entity_types"] = entity_types

        if parsed_since:
            conditions.append("e.created_at >= datetime($since)")
            params["since"] = parsed_since.isoformat()

        if tenant_id:
            conditions.append("e.tenant_id = $tenant_id")
            params["tenant_id"] = tenant_id

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        search_query = f"""
        MATCH (e:Entity)
        {where_clause}
        RETURN properties(e) as props, labels(e) as labels, 'entity' as type
        SKIP $offset
        LIMIT $limit
        """

        result = await graphiti_client.driver.execute_query(search_query, **params)

        items = []
        for r in result.records:
            props = r["props"]
            labels = r["labels"]
            entity_type = next((l for l in labels if l != "Entity"), "Unknown")

            items.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "type": "entity",
                "entity_type": entity_type,
                "summary": props.get("summary", ""),
                "created_at": props.get("created_at")
            })

        # Compute facets
        facets = {
            "entity_types": {},
            "total": len(items)
        }

        for item in items:
            et = item.get("entity_type", "Unknown")
            facets["entity_types"][et] = facets["entity_types"].get(et, 0) + 1

        return {
            "results": items,
            "facets": facets,
            "total": len(items),
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
    current_user: User = Depends(get_current_user)
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
