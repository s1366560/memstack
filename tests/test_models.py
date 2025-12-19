"""Tests for episode models."""

from datetime import datetime

import pytest

from server.models.episode import Episode, EpisodeCreate, SourceType


def test_episode_create_model():
    """Test EpisodeCreate model validation."""
    episode_data = EpisodeCreate(
        content='Test episode content',
        source_type=SourceType.TEXT,
        metadata={'test': 'value'},
    )

    assert episode_data.content == 'Test episode content'
    assert episode_data.source_type == SourceType.TEXT
    assert episode_data.metadata == {'test': 'value'}
    assert episode_data.valid_at is None  # Optional field


def test_episode_create_defaults():
    """Test EpisodeCreate with default values."""
    episode_data = EpisodeCreate(content='Test content')

    assert episode_data.source_type == SourceType.TEXT
    assert episode_data.metadata is None
    assert episode_data.tenant_id is None


def test_episode_model():
    """Test Episode model."""
    now = datetime.utcnow()
    episode = Episode(
        content='Test episode',
        source_type=SourceType.JSON,
        metadata={'key': 'value'},
        valid_at=now,
        tenant_id='tenant_123',
    )

    assert episode.content == 'Test episode'
    assert episode.source_type == SourceType.JSON
    assert episode.metadata == {'key': 'value'}
    assert episode.valid_at == now
    assert episode.tenant_id == 'tenant_123'
    assert episode.id is not None  # Auto-generated UUID
    assert episode.created_at is not None  # Auto-generated timestamp
