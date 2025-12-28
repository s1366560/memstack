from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import logging
from datetime import datetime

from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.secondary.persistence.models import User
from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client

# Use Cases & DI Container
from src.configuration.di_container import DIContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["graphiti"])

# --- Schemas ---

class Entity(BaseModel):
    uuid: str
    name: str
    entity_type: str
    summary: str
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[str] = None

class Community(BaseModel):
    uuid: str
    name: str
    summary: str
    member_count: int
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    formed_at: Optional[str] = None
    created_at: Optional[str] = None

class SearchResult(BaseModel):
    results: List[dict]
    total: int
    search_type: str
    strategy: Optional[str] = None

class GraphData(BaseModel):
    elements: dict

# --- Endpoints ---

@router.post("/search-enhanced/advanced")
async def advanced_search(
    params: dict,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """Advanced search."""
    try:
        query = params.get("query", "")
        project_id = params.get("project_id")
        limit = params.get("limit", 50)
        
        # This is a simplified search implementation
        # Real implementation should use graphiti_client.search_() with proper config
        
        # Reuse existing search logic via custom query if needed, or use client
        # For now, let's just use a simple semantic search if available or return empty with valid format
        
        return {
            "results": [],
            "total": 0,
            "search_type": "hybrid",
            "strategy": params.get("strategy", "hybrid")
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communities/")
async def list_communities(
    project_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """List communities."""
    try:
        conditions = ["coalesce(c.member_count, 0) >= 0"]
        if project_id:
            conditions.append("c.project_id = $project_id")
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (c:Community)
        WHERE {where_clause}
        RETURN properties(c) as props
        ORDER BY coalesce(c.member_count, 0) DESC
        LIMIT $limit
        """
        
        result = await graphiti_client.driver.execute_query(
            query,
            project_id=project_id,
            limit=limit
        )
        
        communities = []
        for r in result.records:
            props = r["props"]
            communities.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "summary": props.get("summary", ""),
                "member_count": props.get("member_count", 0),
                "tenant_id": props.get("tenant_id"),
                "project_id": props.get("project_id"),
                "formed_at": props.get("formed_at"),
                "created_at": props.get("created_at")
            })
            
        return {
            "communities": communities,
            "total": len(communities)
        }
    except Exception as e:
        logger.error(f"Failed to list communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/")
async def list_entities(
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """List entities."""
    try:
        conditions = []
        if project_id:
            project_condition = """
            (
                e.project_id = $project_id OR
                EXISTS {
                    MATCH (e)<-[:MENTIONS]-(ep:Episodic)
                    WHERE ep.project_id = $project_id
                }
            )
            """
            conditions.append(project_condition)
            
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count
        count_query = f"MATCH (e:Entity) {where_clause} RETURN count(e) as total"
        count_result = await graphiti_client.driver.execute_query(count_query, project_id=project_id)
        total = count_result.records[0]["total"] if count_result.records else 0
        
        # List
        list_query = f"""
        MATCH (e:Entity)
        {where_clause}
        RETURN properties(e) as props, labels(e) as labels
        ORDER BY e.created_at DESC
        SKIP $offset
        LIMIT $limit
        """
        
        result = await graphiti_client.driver.execute_query(
            list_query,
            project_id=project_id,
            offset=offset,
            limit=limit
        )
        
        entities = []
        for r in result.records:
            props = r["props"]
            labels = r["labels"]
            e_type = next((l for l in labels if l != "Entity"), "Unknown")
            
            entities.append({
                "uuid": props.get("uuid", ""),
                "name": props.get("name", ""),
                "entity_type": e_type,
                "summary": props.get("summary", ""),
                "tenant_id": props.get("tenant_id"),
                "project_id": props.get("project_id"),
                "created_at": props.get("created_at")
            })
            
        return {
            "entities": entities,
            "total": total
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/graph")
async def get_graph(
    project_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """Get graph data."""
    try:
        # Simple graph query
        query = """
        MATCH (n)
        WHERE ('Entity' IN labels(n) OR 'Episodic' IN labels(n) OR 'Community' IN labels(n))
        AND ($project_id IS NULL OR n.project_id = $project_id)
        
        OPTIONAL MATCH (n)-[r]->(m)
        WHERE ('Entity' IN labels(m) OR 'Episodic' IN labels(m) OR 'Community' IN labels(m))
        
        RETURN 
            elementId(n) as source_id, labels(n) as source_labels, properties(n) as source_props,
            elementId(r) as edge_id, type(r) as edge_type, properties(r) as edge_props,
            elementId(m) as target_id, labels(m) as target_labels, properties(m) as target_props
        LIMIT $limit
        """
        
        result = await graphiti_client.driver.execute_query(
            query,
            project_id=project_id,
            limit=limit
        )
        
        nodes_map = {}
        edges_list = []
        
        for r in result.records:
            s_id = r["source_id"]
            s_props = r["source_props"]
            if "name_embedding" in s_props: del s_props["name_embedding"]
            
            if s_id not in nodes_map:
                nodes_map[s_id] = {
                    "data": {
                        "id": s_id,
                        "label": r["source_labels"][0] if r["source_labels"] else "Entity",
                        "name": s_props.get("name", "Unknown"),
                        **s_props
                    }
                }
                
            if r["target_id"]:
                t_id = r["target_id"]
                t_props = r["target_props"]
                if "name_embedding" in t_props: del t_props["name_embedding"]
                
                if t_id not in nodes_map:
                    nodes_map[t_id] = {
                        "data": {
                            "id": t_id,
                            "label": r["target_labels"][0] if r["target_labels"] else "Entity",
                            "name": t_props.get("name", "Unknown"),
                            **t_props
                        }
                    }
                    
                if r["edge_id"]:
                    e_props = r["edge_props"]
                    if "fact_embedding" in e_props: del e_props["fact_embedding"]
                    
                    edges_list.append({
                        "data": {
                            "id": r["edge_id"],
                            "source": s_id,
                            "target": t_id,
                            "label": r["edge_type"],
                            **e_props
                        }
                    })
        
        return {
            "elements": {
                "nodes": list(nodes_map.values()),
                "edges": edges_list
            }
        }
    except Exception as e:
        logger.error(f"Failed to get graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/search")
async def memory_search(
    params: dict,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """Memory search."""
    try:
        # Stub for now, can implement properly if needed
        return {
            "results": [],
            "total": 0,
            "query": params.get("query", ""),
            "filters_applied": {},
            "search_metadata": {}
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
