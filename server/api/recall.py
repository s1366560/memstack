import logging

from fastapi import APIRouter, Depends, HTTPException

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.models.recall import ShortTermRecallQuery, ShortTermRecallResponse
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recall", tags=["recall"])


@router.post("/short", response_model=ShortTermRecallResponse)
async def short_term_recall(
    payload: ShortTermRecallQuery,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """Recall short-term episodic memories within the given time window."""
    try:
        logger.info(
            f"Short-term recall by user {api_key.user_id}: window={payload.window_minutes}m tenant={payload.tenant_id}"
        )
        return await graphiti.short_term_recall(
            window_minutes=payload.window_minutes, limit=payload.limit, tenant_id=payload.tenant_id
        )
    except Exception as e:
        logger.error(f"Short-term recall failed: {e}")
        raise HTTPException(status_code=500, detail=f"Short-term recall failed: {str(e)}")


@router.post("/communities/rebuild")
async def rebuild_communities(
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """Trigger community rebuild for long-term memory organization."""
    try:
        await graphiti.rebuild_communities()
        return {"status": "ok", "message": "Communities rebuild triggered"}
    except Exception as e:
        logger.error(f"Community rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=f"Community rebuild failed: {str(e)}")

