"""Data export and management API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])


@router.post("/export")
async def export_data(
    tenant_id: Optional[str] = Body(None, description="Filter by tenant ID"),
    include_episodes: bool = Body(True, description="Include episode data"),
    include_entities: bool = Body(True, description="Include entity data"),
    include_relationships: bool = Body(True, description="Include relationship data"),
    include_communities: bool = Body(True, description="Include community data"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Export graph data as JSON.

    Args:
        tenant_id: Optional tenant filter
        include_episodes: Include episode data
        include_entities: Include entity data
        include_relationships: Include relationship data
        include_communities: Include community data
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Exported data in JSON format
    """
    try:
        data = await graphiti.export_data(
            tenant_id=tenant_id,
            include_episodes=include_episodes,
            include_entities=include_entities,
            include_relationships=include_relationships,
            include_communities=include_communities,
        )

        return data
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get graph statistics.

    Returns statistics about the knowledge graph including:
    - Number of entities
    - Number of episodes
    - Number of communities
    - Number of relationships (edges)

    Args:
        tenant_id: Optional tenant filter
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Graph statistics
    """
    try:
        stats = await graphiti.get_graph_stats(tenant_id=tenant_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_data(
    dry_run: bool = Query(True, description="If true, only report what would be deleted"),
    older_than_days: int = Query(90, ge=1, description="Delete data older than this many days"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Clean up old graph data.

    This endpoint can be used to remove old episodes and their associated
    entities and relationships. Use with caution!

    Args:
        dry_run: If true, only report what would be deleted
        older_than_days: Delete data older than this many days
        tenant_id: Optional tenant filter
        graphiti: Graphiti service dependency
        api_key: API key for authentication

    Returns:
        Cleanup report
    """
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Count episodes that would be deleted
        tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""
        count_query = f"""
        MATCH (e:Episodic {tenant_filter})
        WHERE e.created_at < datetime($cutoff_date)
        RETURN count(e) as count
        """
        result = await graphiti.client.driver.execute_query(
            count_query,
            tenant_id=tenant_id,
            cutoff_date=cutoff_date.isoformat(),
        )
        count = result.records[0]["count"] if result.records else 0

        if dry_run:
            return {
                "dry_run": True,
                "would_delete": count,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Would delete {count} episodes older than {older_than_days} days",
            }
        else:
            # Actually delete (DETACH DELETE removes nodes and their relationships)
            delete_query = f"""
            MATCH (e:Episodic {tenant_filter})
            WHERE e.created_at < datetime($cutoff_date)
            DETACH DELETE e
            RETURN count(e) as deleted
            """
            result = await graphiti.client.driver.execute_query(
                delete_query,
                tenant_id=tenant_id,
                cutoff_date=cutoff_date.isoformat(),
            )
            deleted = result.records[0]["deleted"] if result.records else 0

            logger.warning(
                f"Deleted {deleted} episodes older than {older_than_days} days for tenant: {tenant_id}"
            )

            return {
                "dry_run": False,
                "deleted": deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Deleted {deleted} episodes older than {older_than_days} days",
            }
    except Exception as e:
        logger.error(f"Failed to cleanup data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
