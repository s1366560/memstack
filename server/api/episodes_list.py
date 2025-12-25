import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.models.memory import MemoryItem
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("/")
async def list_episodes(
    limit: int = 100,
    since: Optional[str] = None,
    tenant_id: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """List episodic events with optional tenant/project/user filters and since window."""
    try:
        from datetime import datetime

        parsed_since = None
        if since:
            try:
                parsed_since = datetime.fromisoformat(since)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")

        # Reuse short-term recall pipeline for listing episodes
        resp = await graphiti.short_term_recall(
            window_minutes=10_000_000
            if not parsed_since
            else 30,  # large window when since not set
            limit=limit,
            tenant_id=tenant_id,
        )

        # Additional client-side filter
        def passes(item: MemoryItem) -> bool:
            md = item.metadata or {}
            if project_id and md.get("project_id") != project_id:
                return False
            if user_id and md.get("user_id") != user_id:
                return False
            return True

        results = [i for i in resp.results if passes(i)][:limit]
        return {"results": results, "total": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List episodes failed: {e}")
        raise HTTPException(status_code=500, detail=f"List episodes failed: {str(e)}")
