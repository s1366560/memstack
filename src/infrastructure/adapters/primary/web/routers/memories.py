"""Memories API endpoints."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.schemas.auth import User as UserSchema
from src.application.schemas.project import ProjectResponse
from src.infrastructure.adapters.primary.web.dependencies import get_current_user
from src.infrastructure.adapters.secondary.persistence.database import get_db
from src.infrastructure.adapters.secondary.persistence.models import (
    Memory,
    Project,
    User,
    UserProject,
    UserTenant,
)
from src.infrastructure.adapters.primary.web.dependencies import get_graphiti_client, get_queue_service

# Use Cases & DI Container
from src.configuration.di_container import DIContainer

from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["memories"])

# --- Schemas ---

class EntityCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class RelationshipCreate(BaseModel):
    source: str
    target: str
    type: str
    description: Optional[str] = None

class MemoryCreate(BaseModel):
    project_id: str
    title: str
    content: str
    content_type: str = "text"
    tags: List[str] = []
    entities: List[EntityCreate] = []
    relationships: List[RelationshipCreate] = []
    collaborators: List[str] = []
    is_public: bool = False
    metadata: dict = {}

class MemoryResponse(BaseModel):
    id: str
    project_id: str
    title: str
    content: str
    content_type: str
    tags: List[str]
    entities: List[dict]
    relationships: List[dict]
    version: int
    author_id: str
    collaborators: List[str]
    is_public: bool
    status: str
    processing_status: str
    meta: dict = Field(serialization_alias="metadata")
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int
    page: int
    page_size: int

# --- Endpoints ---

@router.post("/memories/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    graphiti_client = Depends(get_graphiti_client),
    queue_service = Depends(get_queue_service),
):
    """Create a new memory."""
    try:
        project_id = memory_data.project_id
        # Verify project access
        result = await db.execute(
            select(UserProject).where(
                UserProject.user_id == current_user.id,
                UserProject.project_id == project_id,
            )
        )
        user_project = result.scalar_one_or_none()
        
        project = None
        if not user_project:
            # Check if project is public or user is owner
            project_result = await db.execute(select(Project).where(Project.id == project_id))
            project = project_result.scalar_one_or_none()
            if not project or project.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this project",
                )
        else:
            if user_project.role == "viewer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Viewers cannot create memories",
                )
            if not project:
                project_result = await db.execute(select(Project).where(Project.id == project_id))
                project = project_result.scalar_one()
    
        # Create memory
        memory_id = str(uuid4())
        
        memory = Memory(
            id=memory_id,
            project_id=project_id,
            title=memory_data.title,
            content=memory_data.content,
            content_type=memory_data.content_type,
            tags=memory_data.tags,
            entities=[e.dict() for e in memory_data.entities],
            relationships=[r.dict() for r in memory_data.relationships],
            author_id=current_user.id,
            collaborators=memory_data.collaborators,
            is_public=memory_data.is_public,
            meta=memory_data.metadata,
            version=1,
            status="ENABLED",
            processing_status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
        db.add(memory)
        
        # Add to Graphiti if enabled
        try:
            # Pre-create EpisodicNode in Neo4j to avoid race conditions
            await graphiti_client.driver.execute_query(
                """
                MERGE (e:Episodic {uuid: $uuid})
                SET e:Node,
                    e.name = $name,
                    e.content = $content,
                    e.source_description = $source_description,
                    e.source = $source,
                    e.created_at = datetime($created_at),
                    e.valid_at = datetime($created_at),
                    e.group_id = $group_id,
                    e.tenant_id = $tenant_id,
                    e.project_id = $project_id,
                    e.user_id = $user_id,
                    e.memory_id = $memory_id,
                    e.status = 'Processing',
                    e.entity_edges = []
                """,
                uuid=memory.id,
                name=memory.title or str(memory.id),
                content=memory.content,
                source_description="User input",
                source="text",
                created_at=memory.created_at.isoformat(),
                group_id=project_id,
                tenant_id=project.tenant_id,
                project_id=project_id,
                user_id=current_user.id,
                memory_id=memory.id,
            )

            await queue_service.add_episode(
                group_id=project_id,
                name=memory.title or str(memory.id),
                content=memory.content,
                source_description="User input",
                episode_type="text",
                entity_types=None,
                uuid=memory.id,
                tenant_id=project.tenant_id,
                project_id=project_id,
                user_id=current_user.id,
                memory_id=memory.id,
            )
            logger.info(f"Memory {memory.id} added to processing queue")
        except Exception as e:
            logger.error(f"Failed to add memory to queue: {e}")
    
        await db.commit()
        await db.refresh(memory)
    
        return MemoryResponse.from_orm(memory)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/", response_model=MemoryListResponse)
async def list_memories(
    project_id: str = Query(..., description="Project ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List memories for a project."""
    # Verify access
    user_project_result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == current_user.id,
            UserProject.project_id == project_id,
        )
    )
    if not user_project_result.scalar_one_or_none():
         # Check ownership
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if not project or project.owner_id != current_user.id:
             # TODO: Check if project is public?
             raise HTTPException(status_code=403, detail="Access denied")

    # Build query
    query = select(Memory).where(Memory.project_id == project_id)

    if search:
        query = query.where(
            or_(
                Memory.title.ilike(f"%{search}%"),
                Memory.content.ilike(f"%{search}%"),
            )
        )

    # Count
    count_query = select(func.count(Memory.id)).where(Memory.project_id == project_id)
    if search:
        count_query = count_query.where(
             or_(
                Memory.title.ilike(f"%{search}%"),
                Memory.content.ilike(f"%{search}%"),
            )
        )
    
    total = (await db.execute(count_query)).scalar()

    # Pagination
    query = query.order_by(Memory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    memories = result.scalars().all()

    return MemoryListResponse(
        memories=[MemoryResponse.from_orm(m) for m in memories],
        total=total or 0,
        page=page,
        page_size=page_size
    )

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific memory."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Check access
    # Simplified: Check if user has access to project
    user_project_result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == current_user.id,
            UserProject.project_id == memory.project_id,
        )
    )
    if not user_project_result.scalar_one_or_none():
        # Check ownership
        project_result = await db.execute(select(Project).where(Project.id == memory.project_id))
        project = project_result.scalar_one_or_none()
        if not project or project.owner_id != current_user.id:
             raise HTTPException(status_code=403, detail="Access denied")

    return MemoryResponse.from_orm(memory)

@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    graphiti_client = Depends(get_graphiti_client),
):
    """Delete a memory."""
    # 1. Get memory to check permissions and project_id
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    # 2. Check permissions
    if memory.author_id != current_user.id:
         # Check if user is project owner/admin
        user_project_result = await db.execute(
            select(UserProject).where(
                UserProject.user_id == current_user.id,
                UserProject.project_id == memory.project_id,
                UserProject.role.in_(["owner", "admin"])
            )
        )
        if not user_project_result.scalar_one_or_none():
             # Check if user is tenant owner? (Optional, skipping for now)
             raise HTTPException(status_code=403, detail="Permission denied")

    # 3. Delete from Graphiti/Neo4j
    try:
        # Delete episode node by memory_id
        # Also delete related edges? DETACH DELETE handles edges connected to the node.
        # We assume the episode node has memory_id property (set in create_memory)
        # If not, we might need to match by uuid (which is same as memory_id in our implementation)
        query = """
        MATCH (e:Episodic {uuid: $uuid})
        DETACH DELETE e
        """
        await graphiti_client.driver.execute_query(query, uuid=memory_id)
        logger.info(f"Deleted episode {memory_id} from graph")
        
    except Exception as e:
        logger.error(f"Failed to delete memory {memory_id} from graph: {e}")
        # We continue to delete from DB even if graph fails, or maybe we should error?
        # Better to log and continue to avoid desync where DB has it but user wants it gone.

    # 4. Delete from SQL Database
    await db.delete(memory)
    await db.commit()
