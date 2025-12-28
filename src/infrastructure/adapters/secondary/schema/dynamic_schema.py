"""
Dynamic schema generation for projects.

This module provides functionality to dynamically create Pydantic models
based on project-specific entity and edge type definitions stored in the database.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, create_model
from sqlalchemy import select

from src.infrastructure.adapters.secondary.persistence.database import async_session_factory
from src.infrastructure.adapters.secondary.persistence.models import (
    EdgeType,
    EdgeTypeMap,
    EntityType,
)


async def get_project_schema(project_id: str) -> Tuple[Dict, Dict, Dict]:
    """
    Get dynamic schema for a project.
    Returns: (entity_types, edge_types, edge_type_map)
    """
    entity_types = {}
    edge_types = {}
    edge_type_map = {}

    # Default types
    for name in [
        "Entity",
        "Person",
        "Organization",
        "Location",
        "Concept",
        "Event",
        "Artifact",
    ]:
        entity_types[name] = create_model(name, __base__=BaseModel)

    if not project_id:
        return entity_types, edge_types, edge_type_map

    async with async_session_factory() as session:
        # Fetch Entity Types
        result = await session.execute(
            select(EntityType).where(EntityType.project_id == project_id)
        )
        for et in result.scalars().all():
            fields = {}
            for field_name, field_def in et.schema.items():
                py_type = str
                desc = ""
                if isinstance(field_def, dict):
                    type_str = field_def.get("type", "String")
                    desc = field_def.get("description", "")
                else:
                    type_str = str(field_def)

                if type_str == "Integer":
                    py_type = int
                elif type_str == "Float":
                    py_type = float
                elif type_str == "Boolean":
                    py_type = bool
                elif type_str == "DateTime":
                    py_type = datetime
                elif type_str == "List":
                    py_type = List
                elif type_str == "Dict":
                    py_type = Dict

                fields[field_name] = (Optional[py_type], Field(None, description=desc))

            entity_types[et.name] = create_model(et.name, **fields, __base__=BaseModel)

        # Fetch Edge Types
        result = await session.execute(
            select(EdgeType).where(EdgeType.project_id == project_id)
        )
        for et in result.scalars().all():
            fields = {}
            for field_name, field_def in et.schema.items():
                py_type = str
                desc = ""
                if isinstance(field_def, dict):
                    type_str = field_def.get("type", "String")
                    desc = field_def.get("description", "")
                else:
                    type_str = str(field_def)

                if type_str == "Integer":
                    py_type = int
                elif type_str == "Float":
                    py_type = float
                elif type_str == "Boolean":
                    py_type = bool
                elif type_str == "DateTime":
                    py_type = datetime

                fields[field_name] = (Optional[py_type], Field(None, description=desc))

            edge_types[et.name] = create_model(et.name, **fields, __base__=BaseModel)

        # Fetch Edge Maps
        result = await session.execute(
            select(EdgeTypeMap).where(EdgeTypeMap.project_id == project_id)
        )
        for em in result.scalars().all():
            key = (em.source_type, em.target_type)
            if key not in edge_type_map:
                edge_type_map[key] = []
            edge_type_map[key].append(em.edge_type)

    return entity_types, edge_types, edge_type_map
