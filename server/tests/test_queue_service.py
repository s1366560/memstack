import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from server.services.queue_service import QueueService
from graphiti_core.nodes import EpisodeType

@pytest.mark.asyncio
async def test_queue_service_add_episode():
    # Setup
    queue_service = QueueService()
    mock_graphiti_client = MagicMock()
    mock_graphiti_client.add_episode = AsyncMock()
    mock_graphiti_client.driver = MagicMock()
    mock_graphiti_client.driver.execute_query = AsyncMock()
    mock_graphiti_client.max_coroutines = 5
    
    await queue_service.initialize(mock_graphiti_client)
    
    # Mock manual update functions to avoid import errors if not in path
    # But since we are mocking client.add_episode, the inner logic won't run unless we run the worker
    # We will verify that the task is added to queue
    
    group_id = "test-group"
    uuid = "test-uuid"
    
    q_size = await queue_service.add_episode(
        group_id=group_id,
        name="Test Episode",
        content="Test Content",
        source_description="Test Source",
        episode_type=EpisodeType.text,
        entity_types={},
        uuid=uuid
    )
    
    assert q_size == 1
    assert queue_service.get_queue_size(group_id) == 1
    
    # Wait a bit for the worker to pick up the task
    await asyncio.sleep(0.1)
    
    # Worker should be running or have run
    # If it processed fast, queue size might be 0 now
    
    # Since worker runs in background, we need to check if mock was called
    # Note: process_episode is defined inside add_episode, so it captures the mock
    # The worker executes the captured function.
    
    mock_graphiti_client.add_episode.assert_called_once()
    call_args = mock_graphiti_client.add_episode.call_args
    assert call_args.kwargs['uuid'] == uuid
    assert call_args.kwargs['group_id'] == group_id
    assert call_args.kwargs['update_communities'] is False

@pytest.mark.asyncio
async def test_queue_service_isolation():
    # Test that different groups have different queues
    queue_service = QueueService()
    mock_graphiti_client = MagicMock()
    await queue_service.initialize(mock_graphiti_client)
    
    await queue_service.add_episode_task("group1", AsyncMock())
    await queue_service.add_episode_task("group2", AsyncMock())
    
    assert queue_service.get_queue_size("group1") == 1 # Worker picked it up? Maybe not yet
    # Actually if worker picks it up immediately, size might be 0.
    # But let's check internal dict
    assert "group1" in queue_service._episode_queues
    assert "group2" in queue_service._episode_queues
    assert queue_service._episode_queues["group1"] is not queue_service._episode_queues["group2"]

@pytest.mark.asyncio
async def test_queue_service_metadata_propagation():
    # Setup
    queue_service = QueueService()
    mock_graphiti_client = MagicMock()
    mock_graphiti_client.add_episode = AsyncMock()
    mock_graphiti_client.driver = MagicMock()
    mock_graphiti_client.driver.execute_query = AsyncMock()
    mock_graphiti_client.max_coroutines = 5
    
    await queue_service.initialize(mock_graphiti_client)
    
    group_id = "test-group"
    uuid = "test-uuid"
    tenant_id = "tenant-1"
    project_id = "project-1"
    user_id = "user-1"
    
    await queue_service.add_episode(
        group_id=group_id,
        name="Test Episode",
        content="Test Content",
        source_description="Test Source",
        episode_type=EpisodeType.text,
        entity_types={},
        uuid=uuid,
        tenant_id=tenant_id,
        project_id=project_id,
        user_id=user_id
    )
    
    # Wait for worker
    await asyncio.sleep(0.1)
    
    # Verify add_episode called
    mock_graphiti_client.add_episode.assert_called_once()
    
    # Verify execute_query called for metadata propagation
    mock_graphiti_client.driver.execute_query.assert_called()
    
    # Find the specific call
    calls = mock_graphiti_client.driver.execute_query.call_args_list
    propagation_call_found = False
    for call in calls:
        kwargs = call.kwargs
        if kwargs.get('uuid') == uuid and kwargs.get('tenant_id') == tenant_id:
            propagation_call_found = True
            break
            
    assert propagation_call_found, "Metadata propagation query not executed"
