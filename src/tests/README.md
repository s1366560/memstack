# Testing Guide

This guide covers how to run and write tests for the MemStack project.

## Test Structure

```
src/tests/
├── conftest.py                          # Pytest configuration and fixtures
├── unit/                                # Unit tests
│   ├── routers/                         # Router tests
│   │   ├── test_episodes_router.py
│   │   ├── test_recall_and_search_routers.py
│   │   ├── test_data_maintenance_tasks_routers.py
│   │   └── test_ai_tools_router.py
│   ├── test_create_memory_use_case.py
│   └── test_search_memory_use_case.py
├── integration/                         # Integration tests
│   ├── test_graphiti_adapter_integration.py
│   └── test_database_integration.py
└── performance/                         # Performance benchmarks
    └── test_benchmarks.py
```

## Running Tests

### Run All Tests
```bash
# Using pytest directly
pytest src/tests/ -v

# Using make (if configured)
make test

# With coverage
pytest src/tests/ --cov=src --cov-report=html
```

### Run Specific Test Categories

#### Unit Tests Only
```bash
pytest src/tests/unit/ -v -m unit
```

#### Integration Tests Only
```bash
pytest src/tests/integration/ -v -m integration
```

#### Performance Tests Only
```bash
pytest src/tests/performance/ -v -m performance
```

### Run Specific Test Files
```bash
# Test specific router
pytest src/tests/unit/routers/test_episodes_router.py -v

# Test integration
pytest src/tests/integration/test_graphiti_adapter_integration.py -v
```

### Run Specific Test Cases
```bash
# Run tests matching pattern
pytest src/tests/ -k "test_create_episode" -v

# Run tests in a class
pytest src/tests/unit/routers/test_episodes_router.py::TestEpisodesRouter -v
```

## Test Fixtures

### Available Fixtures

#### Database Fixtures
- `test_engine` - In-memory SQLite database engine
- `test_db` - Async database session
- `test_user` - Test user object
- `test_tenant` - Test tenant data
- `test_project` - Test project data

#### Graphiti Fixtures
- `mock_graphiti_client` - Mocked Graphiti client
- `mock_queue_service` - Mocked queue service

#### FastAPI Fixtures
- `test_app` - Test FastAPI application
- `client` - Test client for making requests

#### Sample Data Fixtures
- `sample_episode_data` - Sample episode for testing
- `sample_memory_data` - Sample memory for testing
- `sample_entity_data` - Sample entity for testing

### Using Fixtures

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    @pytest.mark.asyncio
    async def test_with_fixtures(self, client, sample_episode_data):
        # Make request using test client
        response = client.post("/api/v1/episodes/", json=sample_episode_data)

        # Assert
        assert response.status_code == 202
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import status

@pytest.mark.unit
class TestMyRouter:
    @pytest.mark.asyncio
    async def test_endpoint_success(self, client, mock_graphiti_client):
        # Arrange
        mock_graphiti_client.some_method = AsyncMock(return_value={...})

        # Act
        response = client.get("/api/v1/endpoint")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "expected_key" in data
```

### Integration Test Example

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.integration
class TestMyIntegration:
    @pytest.mark.asyncio
    async def test_database_operation(self, test_db: AsyncSession):
        # Arrange
        user = User(id="test", email="test@example.com", ...)
        test_db.add(user)
        await test_db.commit()

        # Act
        result = await test_db.execute(select(User).where(User.id == "test"))
        user = result.scalar_one()

        # Assert
        assert user.email == "test@example.com"
```

### Performance Test Example

```python
import pytest
import time

@pytest.mark.performance
class TestMyPerformance:
    @pytest.mark.asyncio
    async def test_endpoint_performance(self, client):
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            response = client.get("/api/v1/endpoint")
            assert response.status_code == 200

        end_time = time.time()
        avg_time = ((end_time - start_time) / iterations) * 1000

        # Assert performance meets requirements
        assert avg_time < 100  # Should be under 100ms
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
async def test_unit_test():
    """Fast test with no external dependencies"""
    pass

@pytest.mark.integration
async def test_integration_test():
    """Test with real database/external services"""
    pass

@pytest.mark.slow
async def test_slow_test():
    """Test that takes a long time to run"""
    pass

@pytest.mark.performance
async def test_performance():
    """Performance benchmark"""
    pass
```

## Mocking

### Mocking Graphiti Client

```python
@pytest.mark.asyncio
async def test_with_mock_graphiti(client, mock_graphiti_client):
    # Configure mock
    mock_graphiti_client.search_ = AsyncMock(
        return_value=Mock(episodes=[], nodes=[])
    )

    # Use in test
    response = client.post("/api/v1/search", json={"query": "test"})

    # Verify mock was called
    mock_graphiti_client.search_.assert_called_once()
```

### Mocking LLM Client

```python
@pytest.mark.asyncio
async def test_with_mock_llm(client, mock_graphiti_client):
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.generate_response = AsyncMock(return_value="Generated text")
    mock_graphiti_client.llm_client = mock_llm

    # Test
    response = client.post("/api/v1/ai/optimize", json={"content": "test"})

    # Assert
    assert response.json()["content"] == "Generated text"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      neo4j:
        image: neo4j:5.26
        env:
          NEO4J_AUTH: neo4j/password
        ports:
          - 7687:7687

      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: password
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,neo4j]"

      - name: Run unit tests
        run: pytest src/tests/unit/ -v -m unit

      - name: Run integration tests
        run: pytest src/tests/integration/ -v -m integration
        env:
          NEO4J_URI: bolt://localhost:7687
          POSTGRES_HOST: localhost
          REDIS_HOST: localhost

      - name: Run performance tests
        run: pytest src/tests/performance/ -v -m performance

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

### 1. Test Isolation
Each test should be independent and not rely on other tests:
```python
# ❌ Bad - relies on test execution order
@pytest.mark.asyncio
async def test_1_create_something(client):
    response = client.post("/create", {...})
    global created_id = response.json()["id"]

@pytest.mark.asyncio
async def test_2_use_created_id(client):
    response = client.get(f"/items/{created_id}")

# ✅ Good - self-contained
@pytest.mark.asyncio
async def test_create_and_get(client):
    create_response = client.post("/create", {...})
    item_id = create_response.json()["id"]

    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
```

### 2. Descriptive Test Names
```python
# ❌ Bad
async def test_it_works():

# ✅ Good
async def test_episode_creation_returns_202_with_processing_status():
```

### 3. Arrange-Act-Assert Pattern
```python
@pytest.mark.asyncio
async def test_create_episode_success(client, mock_graphiti_client, sample_data):
    # Arrange
    mock_graphiti_client.add_episode = AsyncMock()

    # Act
    response = client.post("/api/v1/episodes/", json=sample_data)

    # Assert
    assert response.status_code == 202
    assert response.json()["status"] == "processing"
```

### 4. Use Appropriate Assertions
```python
# ❌ Too generic
assert response.status_code == 200

# ✅ Specific and meaningful
assert response.status_code == status.HTTP_202_ACCEPTED
assert "id" in response.json()
assert response.json()["status"] == "processing"
```

### 5. Test Edge Cases
```python
@pytest.mark.asyncio
class TestEpisodeCreation:
    async def test_success(self, client, sample_data):
        """Test normal case"""
        pass

    async def test_missing_required_field(self, client):
        """Test validation"""
        response = client.post("/api/v1/episodes/", json={})
        assert response.status_code == 422

    async def test_empty_name(self, client):
        """Test auto-generation"""
        data = {"content": "test"}
        response = client.post("/api/v1/episodes/", json=data)
        assert response.status_code == 202

    async def test_service_error(self, client, mock_graphiti_client):
        """Test error handling"""
        mock_graphiti_client.add_episode = AsyncMock(
            side_effect=Exception("DB error")
        )
        response = client.post("/api/v1/episodes/", json={...})
        assert response.status_code == 500
```

## Debugging Tests

### Run with Verbose Output
```bash
pytest src/tests/unit/test_episodes_router.py -vv -s
```

### Drop into Debugger
```python
def test_with_debug():
    import pdb; pdb.set_trace()
    # or
    breakpoint()
    # Code will pause here for debugging
```

### See Print Output
```bash
pytest src/tests/ -s
```

### Run Single Test with Details
```bash
pytest src/tests/unit/test_episodes_router.py::TestEpisodesRouter::test_create_episode_success -vv
```

## Coverage Goals

Target coverage metrics:
- Overall: **70%+**
- Application layer: **80%+**
- Domain layer: **90%+**
- Infrastructure adapters: **60%+**

View coverage report:
```bash
pytest src/tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Tests Fail with "ImportError"
```bash
# Make sure you're in the project root
cd /path/to/memstack

# Install in development mode
pip install -e .
```

### Integration Tests Fail
```bash
# Make sure services are running
make docker-up

# Check service status
make docker-logs
```

### "Asyncio loop is closed" Error
```bash
# Use pytest-asyncio with auto mode
pytest src/tests/ --asyncio-mode=auto
```

### Fixtures Not Found
```bash
# Make sure conftest.py is discoverable
pytest src/tests/ --collect-only

# Verify pytest.ini includes src/tests/
```
