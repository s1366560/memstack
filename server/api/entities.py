"""Entity management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/{entity_id}")
async def get_entity(
    entity_id: str,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get entity details by UUID.

    Args:
        entity_id: Entity UUID
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Entity details
    """
    try:
        entity = await graphiti.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return {
            "uuid": entity.uuid,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "summary": entity.summary,
            "tenant_id": entity.tenant_id,
            "project_id": entity.project_id,
            "created_at": entity.created_at,
            "properties": entity.properties,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_entities(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    List entities with filtering and pagination.

    Args:
        tenant_id: Optional tenant filter
        project_id: Optional project filter
        entity_type: Optional entity type filter
        limit: Maximum items to return
        offset: Pagination offset
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Paginated list of entities
    """
    try:
        result = await graphiti.list_entities(
            tenant_id=tenant_id,
            project_id=project_id,
            entity_type=entity_type,
            limit=limit,
            offset=offset,
        )
        
        # Helper to convert Neo4j types to Python types
        def _convert_val(v):
            if hasattr(v, "isoformat"):
                return v.isoformat()
            return v

        return {
            "entities": [
                {
                    "uuid": e.uuid,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "summary": e.summary,
                    "tenant_id": e.tenant_id,
                    "project_id": e.project_id,
                    "created_at": _convert_val(e.created_at),
                }
                for e in result.items
            ],
            "total": result.total,
            "limit": result.limit,
            "offset": result.offset,
            "has_more": result.has_more,
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum relationships to return"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get relationships for an entity.

    Args:
        entity_id: Entity UUID
        relationship_type: Optional relationship type filter
        limit: Maximum relationships to return
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        List of relationships
    """
    try:
        relationships = await graphiti.get_relationships(
            entity_uuid=entity_id,
            relationship_type=relationship_type,
            limit=limit,
        )

        return {
            "relationships": [
                {
                    "uuid": r.uuid,
                    "source_uuid": r.source_uuid,
                    "target_uuid": r.target_uuid,
                    "relation_type": r.relation_type,
                    "fact": r.fact,
                    "score": r.score,
                    "created_at": r.created_at,
                }
                for r in relationships
            ],
            "total": len(relationships),
        }
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))
