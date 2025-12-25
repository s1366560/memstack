"""API routes for AI tools."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.services import GraphitiService, get_graphiti_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


class OptimizeRequest(BaseModel):
    content: str
    instruction: str = "Improve clarity, fix grammar, and format with Markdown."


class OptimizeResponse(BaseModel):
    content: str


class TitleRequest(BaseModel):
    content: str


class TitleResponse(BaseModel):
    title: str


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_content(
    request: OptimizeRequest,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Optimize content using AI.
    """
    try:
        llm_client = graphiti.client.llm_client

        prompt = f"""
        You are an intelligent writing assistant.
        Please rewrite the following text according to these instructions: {request.instruction}
        
        Original Text:
        {request.content}
        
        Output ONLY the rewritten text. Do not include any explanations or conversational filler.
        """

        response = await llm_client.generate_response(
            messages=[{"role": "user", "content": prompt}]
        )

        return OptimizeResponse(content=response.strip())
    except Exception as e:
        logger.error(f"Failed to optimize content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-title", response_model=TitleResponse)
async def generate_title(
    request: TitleRequest,
    graphiti: GraphitiService = Depends(get_graphiti_service),
    api_key: APIKey = Depends(verify_api_key_dependency),
):
    """
    Generate a title for the content using AI.
    """
    try:
        llm_client = graphiti.client.llm_client

        prompt = f"""
        Generate a concise and descriptive title (max 10 words) for the following text.
        
        Text:
        {request.content[:1000]}...
        
        Output ONLY the title. Do not use quotes.
        """

        response = await llm_client.generate_response(
            messages=[{"role": "user", "content": prompt}]
        )

        # Cleanup quotes if present
        title = response.strip().strip('"').strip("'")

        return TitleResponse(title=title)
    except Exception as e:
        logger.error(f"Failed to generate title: {e}")
        raise HTTPException(status_code=500, detail=str(e))
