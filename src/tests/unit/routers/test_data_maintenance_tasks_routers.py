"""Unit tests for data_export, maintenance, and tasks routers."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from fastapi import status


@pytest.mark.unit
class TestDataExportRouter:
    """Test cases for data_export router endpoints."""

    @pytest.mark.asyncio
    async def test_export_data_all(self, client, mock_graphiti_client):
        """Test exporting all data types."""
        # Mock responses
        mock_result = Mock()
        mock_result.records = []
        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=mock_result)

        # Make request
        response = client.post(
            "/api/v1/data/export",
            json={
                "include_episodes": True,
                "include_entities": True,
                "include_relationships": True,
                "include_communities": True,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "exported_at" in data
        assert "episodes" in data
        assert "entities" in data
        assert "relationships" in data
        assert "communities" in data

    @pytest.mark.asyncio
    async def test_export_data_filter_by_tenant(self, client, mock_graphiti_client):
        """Test exporting data with tenant filter."""
        # Mock response
        mock_result = Mock()
        mock_result.records = []
        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=mock_result)

        # Make request
        response = client.post(
            "/api/v1/data/export",
            json={"tenant_id": "tenant_123", "include_episodes": True},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tenant_id"] == "tenant_123"

    @pytest.mark.asyncio
    async def test_get_graph_stats(self, client, mock_graphiti_client):
        """Test getting graph statistics."""
        # Mock count responses
        def mock_query(query, **kwargs):
            result = Mock()
            if "Entity" in query:
                # records[0]["count"] needs to work
                record = Mock()
                record.__getitem__ = lambda self, key: 100
                result.records = [record]
            elif "Episodic" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: 50
                result.records = [record]
            elif "Community" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: 10
                result.records = [record]
            else:
                record = Mock()
                record.__getitem__ = lambda self, key: 200
                result.records = [record]
            return result

        mock_graphiti_client.driver.execute_query = AsyncMock(side_effect=mock_query)

        # Make request
        response = client.get("/api/v1/data/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "entities" in data
        assert "episodes" in data
        assert "communities" in data
        assert "relationships" in data
        assert "total_nodes" in data

    @pytest.mark.asyncio
    async def test_cleanup_data_dry_run(self, client, mock_graphiti_client):
        """Test data cleanup in dry run mode."""
        # Mock count response
        count_result = Mock()
        count_result.records = [Mock(count=25)]

        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=count_result)

        # Make request
        response = client.post(
            "/api/v1/data/cleanup?dry_run=true&older_than_days=90",
            json={},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dry_run"] is True
        assert data["would_delete"] == 25
        assert "cutoff_date" in data

    @pytest.mark.asyncio
    async def test_cleanup_data_execute(self, client, mock_graphiti_client):
        """Test actual data cleanup execution."""
        # Mock responses
        responses = [
            Mock(records=[Mock(count=10)]),  # Count query
            Mock(records=[Mock(deleted=10)]),  # Delete query
        ]

        mock_graphiti_client.driver.execute_query = AsyncMock(side_effect=responses)

        # Make request
        response = client.post(
            "/api/v1/data/cleanup?dry_run=false&older_than_days=30",
            json={},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dry_run"] is False
        assert data["deleted"] == 10


@pytest.mark.unit
class TestMaintenanceRouter:
    """Test cases for maintenance router endpoints."""

    @pytest.mark.asyncio
    async def test_incremental_refresh(self, client, mock_graphiti_client):
        """Test incremental graph refresh."""
        # Make request
        response = client.post(
            "/api/v1/maintenance/refresh/incremental",
            json={
                "episode_uuids": ["ep_1", "ep_2"],
                "rebuild_communities": False,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["episodes_processed"] == 2

    @pytest.mark.asyncio
    async def test_deduplicate_entities_dry_run(self, client, mock_graphiti_client):
        """Test entity deduplication in dry run mode."""
        # Mock response with duplicates
        mock_records = [
            {
                "name": "Duplicate Entity",
                "entities": [{"uuid": "ent_1"}, {"uuid": "ent_2"}],
            }
        ]

        mock_result = Mock()
        mock_result.records = mock_records
        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=mock_result)

        # Make request
        response = client.post(
            "/api/v1/maintenance/deduplicate",
            json={"similarity_threshold": 0.9, "dry_run": True},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dry_run"] is True
        assert data["duplicates_found"] == 1
        assert "duplicate_groups" in data

    @pytest.mark.asyncio
    async def test_invalidate_stale_edges_dry_run(self, client, mock_graphiti_client):
        """Test stale edge invalidation in dry run mode."""
        # Mock response
        mock_records = [Mock(rel_type="MENTIONS", count=50)]

        mock_result = Mock()
        mock_result.records = mock_records
        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=mock_result)

        # Make request
        response = client.post(
            "/api/v1/maintenance/invalidate-edges",
            json={"days_since_update": 30, "dry_run": True},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dry_run"] is True
        assert data["stale_edges_found"] == 50

    @pytest.mark.asyncio
    async def test_get_maintenance_status(self, client, mock_graphiti_client):
        """Test getting maintenance status."""
        # Mock count responses
        def mock_query(query, **kwargs):
            result = Mock()
            if "Entity" in query:
                result.records = [Mock(count=150)]
            elif "Episodic" in query:
                result.records = [Mock(count=80)]
            elif "Community" in query:
                result.records = [Mock(count=5)]
            else:
                result.records = [Mock(count=20)]
            return result

        mock_graphiti_client.driver.execute_query = AsyncMock(side_effect=mock_query)

        # Make request
        response = client.get("/api/v1/maintenance/status")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "stats" in data
        assert "recommendations" in data
        assert "last_checked" in data

    @pytest.mark.asyncio
    async def test_optimize_graph(self, client, mock_graphiti_client):
        """Test graph optimization with multiple operations."""
        # Mock responses
        mock_result = Mock()
        mock_result.records = []
        mock_graphiti_client.driver.execute_query = AsyncMock(return_value=mock_result)

        # Make request
        response = client.post(
            "/api/v1/maintenance/optimize",
            json={
                "operations": ["incremental_refresh", "deduplicate"],
                "dry_run": True,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "operations_run" in data
        assert data["dry_run"] is True
        assert len(data["operations_run"]) == 2


@pytest.mark.unit
class TestTasksRouter:
    """Test cases for tasks router endpoints."""

    @pytest.mark.asyncio
    async def test_get_task_stats(self, client, test_db):
        """Test getting task statistics."""
        # Make request
        response = client.get("/api/v1/tasks/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "processing" in data
        assert "completed" in data
        assert "failed" in data
        assert "throughput_per_minute" in data
        assert "error_rate" in data

    @pytest.mark.asyncio
    async def test_get_queue_depth(self, client):
        """Test getting queue depth over time."""
        # Make request
        response = client.get("/api/v1/tasks/queue-depth")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "timestamp" in data[0]
        assert "depth" in data[0]

    @pytest.mark.asyncio
    async def test_get_recent_tasks(self, client, test_db):
        """Test getting recent tasks."""
        # Make request
        response = client.get("/api/v1/tasks/recent?limit=10&offset=0")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_status_breakdown(self, client):
        """Test getting task status breakdown."""
        # Make request
        response = client.get("/api/v1/tasks/status-breakdown")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Completed" in data
        assert "Processing" in data
        assert "Failed" in data
        assert "Pending" in data

    @pytest.mark.asyncio
    async def test_retry_task_not_found(self, client, test_db):
        """Test retrying a non-existent task."""
        # Make request
        response = client.post("/api/v1/tasks/nonexistent_task_id/retry")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_stop_task_not_found(self, client, test_db):
        """Test stopping a non-existent task."""
        # Make request
        response = client.post("/api/v1/tasks/nonexistent_task_id/stop")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestMemosRouter:
    """Test cases for memos router endpoints."""

    @pytest.mark.asyncio
    async def test_create_memo_success(self, client, test_db):
        """Test successful memo creation."""
        # Make request
        response = client.post(
            "/memos",
            json={
                "content": "Test memo content",
                "visibility": "PRIVATE",
                "tags": ["tag1", "tag2"],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["content"] == "Test memo content"
        assert data["visibility"] == "PRIVATE"

    @pytest.mark.asyncio
    async def test_list_memos(self, client, test_db):
        """Test listing memos."""
        # Make request
        response = client.get("/memos?limit=10&offset=0")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_memo_not_found(self, client, test_db):
        """Test getting a non-existent memo."""
        # Make request
        response = client.get("/memos/nonexistent_id")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_memo_not_found(self, client, test_db):
        """Test updating a non-existent memo."""
        # Make request
        response = client.patch(
            "/memos/nonexistent_id",
            json={"content": "Updated content"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_memo_not_found(self, client, test_db):
        """Test deleting a non-existent memo."""
        # Make request
        response = client.delete("/memos/nonexistent_id")

        # Assert
        # Could be 404 or 204 depending on implementation
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_204_NO_CONTENT]
