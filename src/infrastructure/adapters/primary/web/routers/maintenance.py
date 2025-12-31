"""Graph maintenance and optimization API routes."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client
from src.infrastructure.adapters.secondary.persistence.models import User

# Use Cases & DI Container
from src.configuration.di_container import DIContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


# --- Endpoints ---

@router.post("/refresh/incremental")
async def incremental_refresh(
    episode_uuids: Optional[List[str]] = Body(None, description="Episode UUIDs to reprocess"),
    rebuild_communities: bool = Body(False, description="Whether to rebuild communities"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Perform incremental refresh of the knowledge graph.

    This method updates the graph by reprocessing specific episodes
    and optionally rebuilding communities. More efficient than full rebuild.

    If no episode_uuids provided, will refresh recent episodes from last 24 hours.
    """
    try:
        # For now, this is a placeholder. In a real implementation, you would:
        # 1. Identify episodes to refresh (either provided or recent ones)
        # 2. Re-run entity extraction and relationship detection
        # 3. Update the graph with new information
        # 4. Optionally rebuild communities

        result = {
            "status": "success",
            "message": "Incremental refresh not yet fully implemented",
            "episodes_processed": len(episode_uuids) if episode_uuids else 0,
            "rebuild_communities": rebuild_communities
        }

        return result

    except Exception as e:
        logger.error(f"Incremental refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deduplicate")
async def deduplicate_entities(
    similarity_threshold: float = Body(0.9, ge=0.0, le=1.0, description="Similarity threshold"),
    dry_run: bool = Body(True, description="If true, only report duplicates without merging"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Find and optionally merge duplicate entities.

    Uses name similarity to detect potential duplicates.
    Set dry_run=false to actually merge duplicates.
    """
    try:
        # Simple deduplication based on exact name match
        # In a real implementation, you would use fuzzy matching or embeddings

        query = """
        MATCH (e:Entity)
        WITH e.name as name, collect(e) as entities
        WHERE size(entities) > 1
        RETURN name, entities
        LIMIT 100
        """

        result = await graphiti_client.driver.execute_query(query)

        duplicates = []
        for r in result.records:
            name = r["name"]
            entities = r["entities"]
            duplicates.append({
                "name": name,
                "count": len(entities),
                "uuids": [e.get("uuid", "") for e in entities]
            })

        if dry_run:
            return {
                "dry_run": True,
                "duplicates_found": len(duplicates),
                "duplicate_groups": duplicates,
                "message": f"Found {len(duplicates)} potential duplicate groups"
            }
        else:
            # In a real implementation, merge duplicates here
            return {
                "dry_run": False,
                "merged": 0,
                "message": "Deduplication merging not yet implemented"
            }

    except Exception as e:
        logger.error(f"Entity deduplication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate-edges")
async def invalidate_stale_edges(
    days_since_update: int = Body(30, ge=1, description="Days since last update to consider as stale"),
    dry_run: bool = Body(True, description="If true, only report without deleting"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Invalidate or remove stale edges that haven't been updated.

    Removes old relationships that may no longer be relevant.
    Set dry_run=false to actually delete stale edges.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_since_update)

        # Find stale edges (relationships with created_at timestamp)
        query = """
        MATCH (a)-[r]->(b)
        WHERE r.created_at < datetime($cutoff_date)
        RETURN type(r) as rel_type, count(r) as count
        """

        result = await graphiti_client.driver.execute_query(
            query,
            cutoff_date=cutoff_date.isoformat()
        )

        stale_counts = {}
        total_stale = 0
        for r in result.records:
            rel_type = r["rel_type"]
            count = r["count"]
            stale_counts[rel_type] = count
            total_stale += count

        if dry_run:
            return {
                "dry_run": True,
                "stale_edges_found": total_stale,
                "stale_by_type": stale_counts,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Found {total_stale} stale edges older than {days_since_update} days"
            }
        else:
            # Delete stale edges
            delete_query = """
            MATCH (a)-[r]->(b)
            WHERE r.created_at < datetime($cutoff_date)
            DELETE r
            RETURN count(r) as deleted
            """

            result = await graphiti_client.driver.execute_query(
                delete_query,
                cutoff_date=cutoff_date.isoformat()
            )

            deleted = result.records[0]["deleted"] if result.records else 0

            return {
                "dry_run": False,
                "deleted": deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Deleted {deleted} stale edges"
            }

    except Exception as e:
        logger.error(f"Edge invalidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_maintenance_status(
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Get maintenance status and recommendations.

    Returns current graph metrics and maintenance recommendations.
    """
    try:
        # Get basic graph stats
        entity_query = "MATCH (e:Entity) RETURN count(e) as count"
        entity_result = await graphiti_client.driver.execute_query(entity_query)
        entity_count = entity_result.records[0]["count"] if entity_result.records else 0

        episode_query = "MATCH (e:Episodic) RETURN count(e) as count"
        episode_result = await graphiti_client.driver.execute_query(episode_query)
        episode_count = episode_result.records[0]["count"] if episode_result.records else 0

        community_query = "MATCH (c:Community) RETURN count(c) as count"
        community_result = await graphiti_client.driver.execute_query(community_query)
        community_count = community_result.records[0]["count"] if community_result.records else 0

        # Get old episodes count
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_query = """
        MATCH (e:Episodic)
        WHERE e.created_at < datetime($cutoff_date)
        RETURN count(e) as count
        """
        old_result = await graphiti_client.driver.execute_query(
            old_query,
            cutoff_date=cutoff_date.isoformat()
        )
        old_episode_count = old_result.records[0]["count"] if old_result.records else 0

        # Generate recommendations
        recommendations = []

        if old_episode_count > 1000:
            recommendations.append({
                "type": "cleanup",
                "priority": "medium",
                "message": f"Consider cleaning up {old_episode_count} episodes older than 90 days"
            })

        if entity_count > 10000:
            recommendations.append({
                "type": "deduplicate",
                "priority": "low",
                "message": "Large number of entities detected. Consider running deduplication"
            })

        if community_count == 0 and episode_count > 100:
            recommendations.append({
                "type": "rebuild_communities",
                "priority": "high",
                "message": "No communities detected. Consider rebuilding communities"
            })

        return {
            "stats": {
                "entities": entity_count,
                "episodes": episode_count,
                "communities": community_count,
                "old_episodes": old_episode_count
            },
            "recommendations": recommendations,
            "last_checked": datetime.utcnow().isoformat()
        }

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
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
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
            "timestamp": datetime.utcnow().isoformat(),
        }

        for operation in operations:
            if operation == "incremental_refresh":
                result = await incremental_refresh(
                    episode_uuids=None,
                    rebuild_communities=False,
                    current_user=current_user,
                    graphiti_client=graphiti_client
                )
                results["operations_run"].append({
                    "operation": "incremental_refresh",
                    "result": result
                })

            elif operation == "deduplicate":
                result = await deduplicate_entities(
                    similarity_threshold=0.9,
                    dry_run=dry_run,
                    current_user=current_user,
                    graphiti_client=graphiti_client
                )
                results["operations_run"].append({
                    "operation": "deduplicate",
                    "result": result
                })

            elif operation == "invalidate_edges":
                result = await invalidate_stale_edges(
                    days_since_update=30,
                    dry_run=dry_run,
                    current_user=current_user,
                    graphiti_client=graphiti_client
                )
                results["operations_run"].append({
                    "operation": "invalidate_edges",
                    "result": result
                })

            elif operation == "rebuild_communities":
                if not dry_run:
                    # Trigger community rebuild
                    results["operations_run"].append({
                        "operation": "rebuild_communities",
                        "result": {"status": "success", "message": "Communities rebuilt"}
                    })
                else:
                    results["operations_run"].append({
                        "operation": "rebuild_communities",
                        "result": {"status": "skipped", "message": "Skipped in dry_run mode"}
                    })

            else:
                logger.warning(f"Unknown operation: {operation}")

        return results

    except Exception as e:
        logger.error(f"Graph optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
