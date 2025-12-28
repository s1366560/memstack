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

class SubgraphRequest(BaseModel):
    node_uuids: List[str]
    include_neighbors: bool = True
    limit: int = 100
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None

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
        
        if not query:
            return {
                "results": [],
                "total": 0,
                "search_type": "hybrid",
                "strategy": params.get("strategy", "hybrid")
            }
            
        # Use Graphiti's search_ method
        import graphiti_core.search.search_config_recipes as recipes
        
        # Determine search config based on strategy if needed, but RRF is good default for deep search
        search_config = recipes.COMBINED_HYBRID_SEARCH_RRF
        
        group_ids = [project_id] if project_id else None
        
        results = await graphiti_client.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
        )
        
        # Format results
        formatted_results = []
        
        # Process Episodes
        if hasattr(results, "episodes") and results.episodes:
            for ep in results.episodes:
                formatted_results.append({
                    "uuid": ep.uuid,
                    "name": getattr(ep, "name", "Memory"),
                    "content": ep.content,
                    "type": "episode",
                    "score": getattr(ep, "score", 0.0),
                    "created_at": getattr(ep, "created_at", None),
                    "metadata": {
                        "source": getattr(ep, "source", "user"),
                        "source_description": getattr(ep, "source_description", ""),
                    }
                })

        # Process Nodes
        if hasattr(results, "nodes") and results.nodes:
            for node in results.nodes:
                formatted_results.append({
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": getattr(node, "summary", ""),
                    "content": getattr(node, "summary", ""), # Fallback for UI
                    "type": "entity",
                    "entity_type": getattr(node, "entity_type", "Unknown"),
                    "score": getattr(node, "score", 0.0),
                    "created_at": getattr(node, "created_at", None),
                    "metadata": {}
                })
                
        # Sort and Limit
        formatted_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        formatted_results = formatted_results[:limit]
        
        return {
            "results": formatted_results,
            "total": len(formatted_results),
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

@router.post("/memory/graph/subgraph")
async def get_subgraph(
    params: SubgraphRequest,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """Get subgraph for specific nodes."""
    try:
        project_id = params.project_id
        
        # Build query to fetch nodes and optional neighbors
        query = """
        MATCH (n)
        WHERE n.uuid IN $node_uuids
        AND ($project_id IS NULL OR n.project_id = $project_id)
        
        WITH n
        """
        
        if params.include_neighbors:
            query += """
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE ('Entity' IN labels(m) OR 'Episodic' IN labels(m) OR 'Community' IN labels(m))
            RETURN 
                elementId(n) as source_id, labels(n) as source_labels, properties(n) as source_props,
                elementId(r) as edge_id, type(r) as edge_type, properties(r) as edge_props,
                elementId(m) as target_id, labels(m) as target_labels, properties(m) as target_props
            LIMIT $limit
            """
        else:
            query += """
            RETURN 
                elementId(n) as source_id, labels(n) as source_labels, properties(n) as source_props,
                null as edge_id, null as edge_type, null as edge_props,
                null as target_id, null as target_labels, null as target_props
            LIMIT $limit
            """
            
        result = await graphiti_client.driver.execute_query(
            query,
            node_uuids=params.node_uuids,
            project_id=project_id,
            limit=params.limit
        )
        
        nodes_map = {}
        edges_list = []
        
        for r in result.records:
            # Process source node
            s_id = r["source_id"]
            if s_id:
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
            
            # Process target node and edge if available
            if r.get("target_id"):
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
                    
                if r.get("edge_id"):
                    e_props = r["edge_props"] or {}
                    if "fact_embedding" in e_props: del e_props["fact_embedding"]
                    
                    # Determine direction based on cypher pattern
                    # We used (n)-[r]-(m), so we need to check start/end node of relationship if we care about direction
                    # But for now, let's just use source/target from query result row
                    
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
        logger.error(f"Failed to get subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/search")
async def memory_search(
    params: dict,
    current_user: User = Depends(get_current_user),
    graphiti_client = Depends(get_graphiti_client)
):
    """
    Search memories using Graphiti's hybrid search.

    Supports semantic search, keyword search, and graph traversal.
    """
    try:
        query = params.get("query", "")
        limit = params.get("limit", 10)
        group_id = params.get("project_id") or params.get("tenant_id")

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Build group_ids list
        group_ids = [group_id] if group_id else None

        # Perform search using Graphiti's search_ method
        import graphiti_core.search.search_config_recipes as recipes

        search_config = recipes.COMBINED_HYBRID_SEARCH_RRF

        results = await graphiti_client.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
        )

        # Convert results to response format
        formatted_results = []
        if hasattr(results, "episodes") and results.episodes:
            for ep in results.episodes:
                formatted_results.append({
                    "uuid": ep.uuid,
                    "name": getattr(ep, "name", ""),
                    "content": ep.content,
                    "type": "episode",
                    "score": getattr(ep, "score", 0.0),
                    "created_at": getattr(ep, "created_at", None),
                    "metadata": {
                        "source": getattr(ep, "source", ""),
                        "source_description": getattr(ep, "source_description", ""),
                    }
                })

        if hasattr(results, "nodes") and results.nodes:
            for node in results.nodes:
                formatted_results.append({
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": getattr(node, "summary", ""),
                    "type": "entity",
                    "entity_type": getattr(node, "entity_type", "Unknown"),
                    "score": getattr(node, "score", 0.0),
                    "created_at": getattr(node, "created_at", None),
                    "metadata": {}
                })

        # Sort by score and limit
        formatted_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        formatted_results = formatted_results[:limit]

        return {
            "results": formatted_results,
            "total": len(formatted_results),
            "query": query,
            "filters_applied": {"group_id": group_id} if group_id else {},
            "search_metadata": {
                "strategy": "COMBINED_HYBRID_SEARCH_RRF",
                "limit": limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
