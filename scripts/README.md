# Scripts Directory

This directory contains utility scripts for the MemStack project.

## Test Data Generation

### Overview

The `generate_test_data.py` script generates realistic test data for the MemStack application. It creates episodes (conversations, interactions, events) that will be automatically processed by Graphiti to extract entities, relationships, and communities.

### Features

- **Multiple Generation Modes**:
  - `random`: Generate diverse random episodes
  - `user-series`: Generate coherent activity pattern for a specific user
  - `collaboration`: Generate team collaboration data for a project

- **Realistic Content**: Templates based on real-world scenarios like:
  - User preferences and settings
  - Task completion and activities
  - Product usage patterns
  - Support interactions
  - Learning and training events

- **Flexible Options**:
  - Specify tenant/project IDs
  - Control data volume
  - Generate time-series data
  - Custom user names and project names

### Prerequisites

1. **Running API Server**: Ensure the MemStack API server is running:
   ```bash
   make dev
   # or
   uv run uvicorn server.main:app --reload
   ```

2. **API Key**: Get your API key from the web interface or create one via API:
   ```bash
   # Default dev key is available when server starts in dev mode
   # Check server logs for the default API key
   ```

3. **Dependencies**: Install required packages:
   ```bash
   pip install httpx
   ```

### Usage

#### Quick Start

Generate 50 random episodes (default):

```bash
python scripts/generate_test_data.py
```

Or using the shell wrapper:

```bash
./scripts/generate_test_data.sh
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-url` | API base URL | `http://localhost:8000/api/v1` |
| `--api-key` | API key for authentication | (from env or default) |
| `--count` | Number of episodes to generate | `50` |
| `--mode` | Generation mode (`random`, `user-series`, `collaboration`) | `random` |
| `--user-name` | User name for user-series mode | Random |
| `--project-name` | Project name for collaboration mode | `Test Project` |
| `--days` | Number of days for time-series modes | `7` |
| `--tenant-id` | Tenant ID to use | Auto-create |
| `--project-id` | Project ID to use | Auto-create |

#### Environment Variables

```bash
export API_URL="http://localhost:8000/api/v1"
export API_KEY="your-api-key-here"
export COUNT=100
export MODE="random"
```

### Examples

#### 1. Random Episodes

Generate 100 diverse random episodes:

```bash
python scripts/generate_test_data.py --count 100 --mode random
```

#### 2. User Activity Series

Generate 14 days of activity for a specific user:

```bash
python scripts/generate_test_data.py \
    --mode user-series \
    --user-name "Alice Johnson" \
    --days 14
```

This creates a realistic daily activity pattern showing:
- Morning tasks and activities
- Afternoon collaborations
- Documentation and review work
- Learning and training events

#### 3. Project Collaboration

Generate 30 days of team collaboration data:

```bash
python scripts/generate_test_data.py \
    --mode collaboration \
    --project-name "Alpha Research Project" \
    --days 30
```

This simulates a 5-person team working together with:
- Coordinated project activities
- Team meetings and discussions
- Handoffs between team members
- Documentation and review cycles

#### 4. Custom Tenant/Project

Generate data for a specific tenant and project:

```bash
python scripts/generate_test_data.py \
    --tenant-id "tenant-abc-123" \
    --project-id "project-xyz-789" \
    --count 200
```

#### 5. Using Shell Wrapper

```bash
# Set environment variables
export API_KEY="ms_sk_your_api_key_here"
export COUNT=100

# Run the script
./scripts/generate_test_data.sh --mode random
```

### What Gets Created

#### Episodes

Each episode contains:
- **Content**: Natural language description of an event/activity
- **Name**: Descriptive title
- **Metadata**: Test data markers (batch_id, index, etc.)
- **Timestamp**: When the event occurred (can be historical)
- **Source Type**: Usually "text"

#### Automatically Extracted (by Graphiti)

When episodes are processed, Graphiti automatically extracts:
- **Entities**: People, organizations, products, features, etc.
- **Relationships**: How entities relate to each other
- **Communities**: Groups of related entities

### Sample Output

```
2024-12-24 15:32:10 - __main__ - INFO - Generating 50 episodes...
2024-12-24 15:32:11 - __main__ - INFO - Created 10/50 episodes
2024-12-24 15:32:12 - __main__ - INFO - Created 20/50 episodes
...
2024-12-24 15:32:20 - __main__ - INFO - Successfully created 50/50 episodes
2024-12-24 15:32:20 - __main__ - INFO - Test data generation complete!
```

### Generated Data Examples

#### Random Episode Example
```
Content: "User Alice Johnson prefers dark mode in the application settings."
Name: "Test Episode 1"
Metadata: {"test_data": true, "batch_id": "...", "index": 0}
```

#### User Series Example
```
Content: "Alice Johnson analyzed data trends in the morning."
Name: "Alice Johnson - Day 1 - Activity 1"
Metadata: {"test_data": true, "user_series": "Alice Johnson", "day": 0, "episode_number": 0}
```

#### Collaboration Example
```
Content: "Team meeting: Bob Smith presented Alpha Research requirements analysis."
Name: "Alpha Research - Day 1 - Event"
Metadata: {"test_data": true, "project_name": "Alpha Research", "team_member": "Bob Smith", "collaboration_type": "project_work"}
```

### Troubleshooting

#### Connection Refused

```
httpx.ConnectError: [Errno 61] Connection refused
```

**Solution**: Ensure the API server is running:
```bash
make dev
```

#### Authentication Error

```
401 Unauthorized
```

**Solution**: Check your API key:
```bash
# Find default key in server logs or create a new one
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer <default-key>"
```

#### Import Error

```
ModuleNotFoundError: No module named 'httpx'
```

**Solution**: Install dependencies:
```bash
pip install httpx
```

### Advanced Usage

#### Batch Generation

Generate multiple batches with different parameters:

```bash
#!/bin/bash

# Batch 1: Random episodes
python scripts/generate_test_data.py --count 100 --mode random

# Batch 2: User activities for multiple users
for user in "Alice Johnson" "Bob Smith" "Carol Williams"; do
    python scripts/generate_test_data.py \
        --mode user-series \
        --user-name "$user" \
        --days 14
done

# Batch 3: Multiple projects
for project in "Alpha" "Beta" "Gamma"; do
    python scripts/generate_test_data.py \
        --mode collaboration \
        --project-name "$project" \
        --days 30
done
```

#### Verify Generated Data

Check the created episodes via API:

```bash
curl http://localhost:8000/api/v1/episodes-enhanced/ \
  -H "Authorization: Bearer <your-api-key>"
```

Or view in the web interface:
- Navigate to your project
- Check the Episodes/Memory section
- Filter by "Test Episode" or specific user names

### Integration with Testing

Use in test setup:

```python
import pytest
from scripts.generate_test_data import TestDataGenerator

@pytest.fixture
async def test_data():
    async with TestDataGenerator(api_key="test-key") as gen:
        episodes = await gen.generate_episodes(count=10)
        yield episodes
```

## Contributing

When adding new scripts:

1. Add executable permissions: `chmod +x scripts/your-script.sh`
2. Update this README with usage examples
3. Follow Python best practices (type hints, docstrings)
4. Include error handling and logging
