"""Community management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/communities", tags=["communities"])


@router.get("/{community_id}")
async def get_community(
    community_id: str,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get community details by UUID.

    Args:
        community_id: Community UUID
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Community details
    """
    try:
        community = await graphiti.get_community(community_id)
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        return {
            "uuid": community.uuid,
            "name": community.name,
            "summary": community.summary,
            "member_count": community.member_count,
            "tenant_id": community.tenant_id,
            "project_id": community.project_id,
            "formed_at": community.formed_at,
            "created_at": community.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get community: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_communities(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    min_members: int = Query(0, ge=0, description="Minimum member count"),
    limit: int = Query(50, ge=1, le=200, description="Maximum communities to return"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    List communities with filtering.

    Args:
        tenant_id: Optional tenant filter
        project_id: Optional project filter
        min_members: Minimum member count
        limit: Maximum communities to return
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        List of communities
    """
    try:
        communities = await graphiti.list_communities(
            tenant_id=tenant_id,
            project_id=project_id,
            min_members=min_members,
            limit=limit,
        )

        return {
            "communities": [
                {
                    "uuid": c.uuid,
                    "name": c.name,
                    "summary": c.summary,
                    "member_count": c.member_count,
                    "tenant_id": c.tenant_id,
                    "project_id": c.project_id,
                    "formed_at": c.formed_at,
                    "created_at": c.created_at,
                }
                for c in communities
            ],
            "total": len(communities),
        }
    except Exception as e:
        logger.error(f"Failed to list communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{community_id}/members")
async def get_community_members(
    community_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum members to return"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get entities in a community.

    Args:
        community_id: Community UUID
        limit: Maximum members to return
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        List of entities in the community
    """
    try:
        entities = await graphiti.get_community_members(
            community_uuid=community_id,
            limit=limit,
        )

        return {
            "community_uuid": community_id,
            "members": [
                {
                    "uuid": e.uuid,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "summary": e.summary,
                    "tenant_id": e.tenant_id,
                    "project_id": e.project_id,
                    "created_at": e.created_at,
                }
                for e in entities
            ],
            "total": len(entities),
        }
    except Exception as e:
        logger.error(f"Failed to get community members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild")
async def rebuild_communities(
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Trigger community rebuild using Graphiti's community builder.

    This will re-run the community detection algorithm to identify
    new communities and update existing ones.

    Args:
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Rebuild status
    """
    try:
        await graphiti.rebuild_communities()
        return {
            "status": "success",
            "message": "Community rebuild triggered successfully"
        }
    except Exception as e:
        logger.error(f"Failed to rebuild communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
