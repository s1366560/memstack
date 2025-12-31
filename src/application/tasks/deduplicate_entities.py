"""Deduplicate entities task handler for merging duplicate entities."""

import logging
from typing import Any, Dict

from graphiti_core.nodes import EntityNode
from graphiti_core.utils.maintenance.dedup_helpers import (
    _build_candidate_indexes,
    _resolve_with_similarity,
    DedupResolutionState,
)

from src.domain.tasks.base import TaskHandler

logger = logging.getLogger(__name__)


class DeduplicateEntitiesTaskHandler(TaskHandler):
    """Handler for deduplication tasks."""

    @property
    def task_type(self) -> str:
        return "deduplicate_entities"

    @property
    def timeout_seconds(self) -> int:
        return 1800  # 30 minutes

    async def process(self, payload: Dict[str, Any], context: Any) -> None:
        """Find and merge duplicate entities."""
        queue_service = context
        graphiti_client = queue_service._graphiti_client

        similarity_threshold = payload.get("similarity_threshold", 0.9)
        dry_run = payload.get("dry_run", True)
        group_id = payload.get("group_id", "global")
        project_id = payload.get("project_id")

        try:
            # Step 1: Get all entities in group
            entities = await EntityNode.get_by_group_ids(
                graphiti_client.driver,
                [group_id] if group_id != "global" else None
            )

            logger.info(f"Found {len(entities)} entities for deduplication")

            if len(entities) < 2:
                logger.info("Not enough entities to deduplicate")
                return

            # Step 2: Use Graphiti's deduplication to find duplicates
            indexes = _build_candidate_indexes(entities)
            state = DedupResolutionState(
                resolved_nodes=[None] * len(entities),
                uuid_map={},
                unresolved_indices=list(range(len(entities))),
            )

            # Run similarity-based deduplication
            _resolve_with_similarity(entities, indexes, state)

            # Collect duplicate pairs from state
            # Check what attributes are available in state
            duplicate_pairs = []
            uuid_map = getattr(state, 'uuid_map', {})

            # Find duplicates by checking which original UUIDs map to duplicates
            for dup_uuid, orig_uuid in uuid_map.items():
                if dup_uuid != orig_uuid:
                    # Find the actual entity objects
                    duplicate = next((e for e in entities if e.uuid == dup_uuid), None)
                    original = next((e for e in entities if e.uuid == orig_uuid), None)
                    if duplicate and original:
                        duplicate_pairs.append((duplicate, original))

            logger.info(f"Found {len(duplicate_pairs)} duplicate pairs")

            if dry_run:
                logger.info("Dry run mode - not merging duplicates")
                return

            # Step 3: Merge duplicates
            merged_count = 0
            for duplicate, original in duplicate_pairs:
                try:
                    await self._merge_entities(
                        graphiti_client.driver,
                        duplicate.uuid,
                        original.uuid,
                        project_id
                    )
                    merged_count += 1
                except Exception as e:
                    logger.error(f"Failed to merge {duplicate.uuid} into {original.uuid}: {e}")

            logger.info(f"Merged {merged_count} duplicate entities")

        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            raise

    async def _merge_entities(
        self, driver, duplicate_uuid: str,
        original_uuid: str, project_id: str | None
    ):
        """Merge duplicate entity into original entity.

        This involves:
        1. Redirecting all relationships from duplicate to original
        2. Merging community memberships
        3. Deleting the duplicate node
        4. Preserving metadata
        """
        # Redirect relationships (avoid creating duplicates)
        redirect_query = """
        MATCH (duplicate {uuid: $duplicate_uuid})-[r]-(other)
        WHERE NOT (original {uuid: $original_uuid})-[:RELATES_TO]-(other)
        WITH duplicate, r, other, original
        MATCH (original {uuid: $original_uuid})
        CREATE (original)-[rel:RELATES_TO]->(other)
        SET rel += properties(r)
        DELETE r
        """

        await driver.execute_query(
            redirect_query,
            duplicate_uuid=duplicate_uuid,
            original_uuid=original_uuid
        )

        # Handle community memberships
        community_query = """
        MATCH (duplicate {uuid: $duplicate_uuid})-[:BELONGS_TO]->(c:Community)
        MATCH (original {uuid: $original_uuid})
        MERGE (original)-[:BELONGS_TO]->(c)
        """

        await driver.execute_query(
            community_query,
            duplicate_uuid=duplicate_uuid,
            original_uuid=original_uuid
        )

        # Preserve metadata before deletion
        if project_id:
            metadata_query = """
            MATCH (duplicate {uuid: $duplicate_uuid})
            MATCH (original {uuid: $original_uuid})
            SET original.project_id = coalesce(original.project_id, duplicate.project_id)
            DELETE duplicate
            """
        else:
            metadata_query = """
            MATCH (duplicate {uuid: $duplicate_uuid})
            DELETE duplicate
            """

        await driver.execute_query(
            metadata_query,
            duplicate_uuid=duplicate_uuid,
            original_uuid=original_uuid,
            project_id=project_id
        )
