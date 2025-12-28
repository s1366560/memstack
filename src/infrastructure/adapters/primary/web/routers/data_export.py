"""Data export and management API routes."""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client
from src.infrastructure.adapters.secondary.persistence.models import User

# Use Cases & DI Container
from src.configuration.di_container import DIContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["data"])


# --- Endpoints ---

@router.post("/export")
async def export_data(
    tenant_id: Optional[str] = Body(None, description="Filter by tenant ID"),
    include_episodes: bool = Body(True, description="Include episode data"),
    include_entities: bool = Body(True, description="Include entity data"),
    include_relationships: bool = Body(True, description="Include relationship data"),
    include_communities: bool = Body(True, description="Include community data"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Export graph data as JSON.
    """
    try:
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "episodes": [],
            "entities": [],
            "relationships": [],
            "communities": []
        }

        tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""

        if include_episodes:
            episode_query = f"""
            MATCH (e:Episodic {tenant_filter})
            RETURN properties(e) as props
            ORDER BY e.created_at DESC
            """

            result = await graphiti_client.driver.execute_query(
                episode_query,
                tenant_id=tenant_id
            )

            for r in result.records:
                data["episodes"].append(r["props"])

        if include_entities:
            entity_query = f"""
            MATCH (e:Entity {tenant_filter})
            RETURN properties(e) as props, labels(e) as labels
            """

            result = await graphiti_client.driver.execute_query(
                entity_query,
                tenant_id=tenant_id
            )

            for r in result.records:
                props = r["props"]
                props["labels"] = r["labels"]
                data["entities"].append(props)

        if include_relationships:
            rel_query = f"""
            MATCH (a)-[r]->(b)
            WHERE ('Entity' IN labels(a) OR 'Episodic' IN labels(a) OR 'Community' IN labels(a))
            AND ('Entity' IN labels(b) OR 'Episodic' IN labels(b) OR 'Community' IN labels(b))
            """

            if tenant_id:
                rel_query += " AND a.tenant_id = $tenant_id"

            rel_query += " RETURN properties(r) as props, type(r) as rel_type, elementId(r) as edge_id"

            result = await graphiti_client.driver.execute_query(
                rel_query,
                tenant_id=tenant_id
            )

            for r in result.records:
                data["relationships"].append({
                    "edge_id": r["edge_id"],
                    "type": r["rel_type"],
                    "properties": r["props"]
                })

        if include_communities:
            community_query = f"""
            MATCH (c:Community {tenant_filter})
            RETURN properties(c) as props
            ORDER BY c.member_count DESC
            """

            result = await graphiti_client.driver.execute_query(
                community_query,
                tenant_id=tenant_id
            )

            for r in result.records:
                data["communities"].append(r["props"])

        return data

    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Get graph statistics.

    Returns statistics about the knowledge graph including:
    - Number of entities
    - Number of episodes
    - Number of communities
    - Number of relationships (edges)
    """
    try:
        tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""

        # Entity count
        entity_query = f"""
        MATCH (e:Entity {tenant_filter})
        RETURN count(e) as count
        """
        entity_result = await graphiti_client.driver.execute_query(
            entity_query,
            tenant_id=tenant_id
        )
        entity_count = entity_result.records[0]["count"] if entity_result.records else 0

        # Episode count
        episode_query = f"""
        MATCH (e:Episodic {tenant_filter})
        RETURN count(e) as count
        """
        episode_result = await graphiti_client.driver.execute_query(
            episode_query,
            tenant_id=tenant_id
        )
        episode_count = episode_result.records[0]["count"] if episode_result.records else 0

        # Community count
        community_query = f"""
        MATCH (c:Community {tenant_filter})
        RETURN count(c) as count
        """
        community_result = await graphiti_client.driver.execute_query(
            community_query,
            tenant_id=tenant_id
        )
        community_count = community_result.records[0]["count"] if community_result.records else 0

        # Relationship count
        rel_query = """
        MATCH (a)-[r]->(b)
        WHERE ('Entity' IN labels(a) OR 'Episodic' IN labels(a) OR 'Community' IN labels(a))
        AND ('Entity' IN labels(b) OR 'Episodic' IN labels(b) OR 'Community' IN labels(b))
        """

        if tenant_id:
            rel_query += " AND a.tenant_id = $tenant_id"

        rel_query += " RETURN count(r) as count"

        rel_result = await graphiti_client.driver.execute_query(
            rel_query,
            tenant_id=tenant_id
        )
        rel_count = rel_result.records[0]["count"] if rel_result.records else 0

        return {
            "entities": entity_count,
            "episodes": episode_count,
            "communities": community_count,
            "relationships": rel_count,
            "total_nodes": entity_count + episode_count + community_count,
            "tenant_id": tenant_id
        }

    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_data(
    dry_run: bool = Query(True, description="If true, only report what would be deleted"),
    older_than_days: int = Query(90, ge=1, description="Delete data older than this many days"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Clean up old graph data.

    This endpoint can be used to remove old episodes and their associated
    entities and relationships. Use with caution!
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Count episodes that would be deleted
        tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""
        count_query = f"""
        MATCH (e:Episodic {tenant_filter})
        WHERE e.created_at < datetime($cutoff_date)
        RETURN count(e) as count
        """
        result = await graphiti_client.driver.execute_query(
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
            result = await graphiti_client.driver.execute_query(
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
