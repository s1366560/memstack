# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MemStack is an enterprise-grade AI Memory Cloud Platform built on the open-source Graphiti framework. It provides long-term and short-term memory management for AI applications with knowledge graph integration, temporal awareness, and high-performance retrieval.

## Architecture

The system is organized into three main components:

1. **Backend API Server** (`/server/`) - FastAPI-based REST API
2. **Python SDK** (`/sdk/python/memstack/`) - Client library for programmatic access
3. **Web Console** (`/web/`) - React TypeScript management UI

### Key Architectural Patterns

- **Service Layer Pattern**: Business logic is in `server/services/graphiti_service.py` (the 68KB core), separated from API endpoints in `server/api/`
- **Dependency Injection**: FastAPI's DI container manages service lifecycles
- **Async/Await**: Full async stack using `asyncpg` for PostgreSQL, async Redis, and async HTTP clients
- **Multi-tenant Data Isolation**: Tenants and projects provide logical separation of data
- **Vendored Dependencies**: Graphiti framework is included in `/vendor/graphiti/` for version consistency

### Data Flow

1. **Episode Ingestion**: Episodes (conversations/interactions) are created via API → Graphiti service extracts entities/relationships → Knowledge graph stored in Neo4j → Metadata in PostgreSQL
2. **Memory Retrieval**: Search query → Graphiti performs hybrid search (semantic + keyword + graph traversal) → Results ranked and cached via Redis

## Development Commands

### Backend (Python)

```bash
# Install all dependencies
make install

# Development server with hot reload (http://localhost:8000)
make dev

# Run tests with coverage (50%+ threshold)
make test

# Unit tests only (faster)
make test-unit

# Integration tests only (requires databases)
make test-integration

# Format code with ruff
make format

# Lint + type check
make lint

# Production server (4 workers)
make serve
```

### Frontend (React)

```bash
cd web

# Install dependencies
npm install

# Dev server (http://localhost:5173)
npm run dev

# Production build
npm run build

# Run tests
npm test
npm run test:coverage

# Type checking
npm run type-check

# Linting
npm run lint
```

### Infrastructure

```bash
# Start all services (Neo4j, PostgreSQL, Redis)
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs

# Database migrations
make db-upgrade      # Apply migrations
make db-downgrade    # Rollback one migration
make db-revision     # Create new migration
```

## Technology Stack

### Backend
- **FastAPI** 0.104+ - Async web framework
- **Graphiti** - Knowledge graph engine (vendored)
- **Neo4j** 5.26+ - Graph database
- **PostgreSQL** 16+ - Metadata storage
- **Redis** 7+ - Caching
- **SQLAlchemy** + **asyncpg** - Async ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **uv** - Python package manager

### LLM Providers
The system supports multiple LLM providers, selectable via `LLM_PROVIDER` environment variable:

- **Gemini** (default): `GEMINI_API_KEY`, uses `gemini-2.5-flash`
- **Qwen** (通义千问): `DASHSCOPE_API_KEY`, uses DashScope SDK
- **OpenAI**: Optional embedding support via `OPENAI_API_KEY`

Qwen-specific clients in `server/llm_clients/`:
- `qwen_client.py` - Main LLM interface
- `qwen_embedder.py` - Embedding generation
- `qwen_reranker_client.py` - Result reranking

### Frontend
- **React** 19.2.3
- **TypeScript** 5.9.3
- **Vite** 7.3.0
- **Ant Design** 6.1.1
- **Zustand** 5.0.9 - State management
- **Cytoscape** 3.33.1 - Graph visualization
- **Vitest** - Testing

## Configuration

Configuration is centralized in `server/config.py` using Pydantic Settings. Key environment variables:

```bash
# Services
NEO4J_URI=bolt://localhost:7687
POSTGRES_HOST=localhost
REDIS_HOST=localhost

# LLM Provider (choose one)
LLM_PROVIDER=gemini  # or qwen
GEMINI_API_KEY=xxx
DASHSCOPE_API_KEY=xxx  # for Qwen

# Security
SECRET_KEY=your_secret_key_here
```

The `.env` file is automatically loaded. See `server/config.py` for all available settings.

## API Structure

Base URL: `/api/v1`

- `POST /auth/keys` - Create API key
- `GET /auth/keys` - List API keys
- `DELETE /auth/keys/{id}` - Delete API key
- `POST /episodes/` - Create episode
- `GET /episodes/` - List episodes
- `GET /episodes/{id}` - Get episode details
- `POST /memory/search` - Search memories
- `POST /recall` - Recall relevant memories
- CRUD operations for entities and communities in `server/api/entities.py` and `server/api/communities.py`

## Authentication

API Key-based authentication:
- Format: `ms_sk_<64-char-hex>`
- Keys are SHA256 hashed before storage
- Bearer token in `Authorization` header
- Default key auto-generated in development mode

## Testing Strategy

- **Coverage Target**: 50%+ overall
- **Test Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **Unit Tests**: Fast, isolated, mock external dependencies
- **Integration Tests**: Full stack with live databases
- Run individual tests: `uv run pytest tests/test_specific.py::test_function -v`

## Vendored Dependencies

`/vendor/graphiti/` contains the Graphiti framework to ensure version consistency. When working with Graphiti:
- Prefer using the service layer in `server/services/graphiti_service.py`
- Direct Graphiti imports should reference the vendored path
- See `/vendor/graphiti/CLAUDE.md` for Graphiti-specific guidance

## Common Workflows

### Adding a New API Endpoint
1. Create Pydantic models in `server/models/`
2. Add business logic in `server/services/` or `graphiti_service.py`
3. Create route in `server/api/`
4. Register in `server/main.py`
5. Add tests in `tests/`

### Database Schema Changes
1. Modify SQLAlchemy models in `server/models/`
2. Run `make db-revision message="describe change"`
3. Review generated migration in `alembic/versions/`
4. Run `make db-upgrade`

### Switching LLM Provider
1. Set `LLM_PROVIDER=qwen` or `LLM_PROVIDER=gemini` in `.env`
2. Provide corresponding API key (`DASHSCOPE_API_KEY` or `GEMINI_API_KEY`)
3. Restart server
4. The appropriate client is instantiated automatically in `graphiti_service.py`
