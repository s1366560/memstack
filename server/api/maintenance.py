"""Graph maintenance and optimization API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Query

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/refresh/incremental")
async def incremental_refresh(
    episode_uuids: Optional[List[str]] = Body(None, description="Episode UUIDs to reprocess"),
    rebuild_communities: bool = Body(False, description="Whether to rebuild communities"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Perform incremental refresh of the knowledge graph.

    This method updates the graph by reprocessing specific episodes
    and optionally rebuilding communities. More efficient than full rebuild.

    If no episode_uuids provided, will refresh recent episodes from last 24 hours.
    """
    try:
        result = await graphiti.perform_incremental_refresh(
            episode_uuids=episode_uuids,
            rebuild_communities=rebuild_communities,
        )
        return result
    except Exception as e:
        logger.error(f"Incremental refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deduplicate")
async def deduplicate_entities(
    similarity_threshold: float = Body(0.9, ge=0.0, le=1.0, description="Similarity threshold"),
    dry_run: bool = Body(True, description="If true, only report duplicates without merging"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Find and optionally merge duplicate entities.

    Uses name similarity to detect potential duplicates.
    Set dry_run=false to actually merge duplicates.
    """
    try:
        result = await graphiti.deduplicate_entities(
            similarity_threshold=similarity_threshold,
            dry_run=dry_run,
        )
        return result
    except Exception as e:
        logger.error(f"Entity deduplication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate-edges")
async def invalidate_stale_edges(
    days_since_update: int = Body(30, ge=1, description="Days since last update to consider as stale"),
    dry_run: bool = Body(True, description="If true, only report without deleting"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Invalidate or remove stale edges that haven't been updated.

    Removes old relationships that may no longer be relevant.
    Set dry_run=false to actually delete stale edges.
    """
    try:
        result = await graphiti.invalidate_stale_edges(
            days_since_update=days_since_update,
            dry_run=dry_run,
        )
        return result
    except Exception as e:
        logger.error(f"Edge invalidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_maintenance_status(
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Get maintenance status and recommendations.

    Returns current graph metrics and maintenance recommendations.
    """
    try:
        status = await graphiti.get_maintenance_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get maintenance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_graph(
    operations: List[str] = Body(
        ["incremental_refresh", "deduplicate"],
        description="List of operations to run",
    ),
    dry_run: bool = Body(True, description="If true, report actions without executing"),
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Run multiple optimization operations.

    Supported operations:
    - incremental_refresh: Refresh recent episodes
    - deduplicate: Remove duplicate entities
    - invalidate_edges: Remove stale edges
    - rebuild_communities: Rebuild community structure
    """
    try:
        results = {
            "operations_run": [],
            "dry_run": dry_run,
            "timestamp": None,
        }

        for operation in operations:
            if operation == "incremental_refresh":
                result = await graphiti.perform_incremental_refresh(
                    rebuild_communities=False,
                )
                results["operations_run"].append({
                    "operation": "incremental_refresh",
                    "result": result,
                })

            elif operation == "deduplicate":
                result = await graphiti.deduplicate_entities(dry_run=dry_run)
                results["operations_run"].append({
                    "operation": "deduplicate",
                    "result": result,
                })

            elif operation == "invalidate_edges":
                result = await graphiti.invalidate_stale_edges(dry_run=dry_run)
                results["operations_run"].append({
                    "operation": "invalidate_edges",
                    "result": result,
                })

            elif operation == "rebuild_communities":
                if not dry_run:
                    await graphiti.rebuild_communities()
                    results["operations_run"].append({
                        "operation": "rebuild_communities",
                        "result": {"status": "success", "message": "Communities rebuilt"},
                    })
                else:
                    results["operations_run"].append({
                        "operation": "rebuild_communities",
                        "result": {"status": "skipped", "message": "Skipped in dry_run mode"},
                    })

            else:
                logger.warning(f"Unknown operation: {operation}")

        return results
    except Exception as e:
        logger.error(f"Graph optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
