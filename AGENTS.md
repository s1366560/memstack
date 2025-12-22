# VIP Memory Repository Guidelines

## Project Structure & Module Organization
VIP Memory is a knowledge graph-based memory system built on FastAPI and Graphiti. The project structure follows a three-tier architecture:

- **Server** (`server/`): FastAPI backend with authentication, API routes, and Graphiti service integration
  - `api/`: REST endpoints for episodes and memory search
  - `services/`: Graphiti service wrapper and dependency injection
  - `models/`: Pydantic models for requests/responses (auth, episodes, memory, entities)
  - `llm_clients/`: LLM provider integrations (Qwen, embeddings, rerankers)
  - `auth.py`: API Key authentication middleware
  - `config.py`: Environment-based configuration
  - `main.py`: FastAPI application entry point

- **SDK** (`sdk/python/`): Python client library for programmatic access
  - `vip_memory/client.py`: Synchronous HTTP client with retry logic
  - `vip_memory/async_client.py`: Async/await client for high-performance applications  
  - `vip_memory/models.py`: Request/response models mirroring server schemas
  - `vip_memory/exceptions.py`: Client error hierarchy

- **Web Console** (`web/`): React-based management interface
  - Built with Vite, TypeScript, Ant Design
  - Independent deployment via Nginx reverse proxy
  - API authentication via localStorage token

- **Tests** (`tests/`): Comprehensive test suite covering authentication, APIs, SDK, and services
  - Unit tests with mocking for isolated component testing
  - Integration tests marked with `@pytest.mark.integration`
  - Coverage targeting 50%+ with pytest-cov

## Build, Test, and Development Commands
- `uv sync --extra dev`: Install development environment with all dependencies
- `make test`: Run full test suite with coverage (must pass 50% threshold)
- `make test-unit`: Run unit tests only (fast, no external dependencies)
- `make test-integration`: Run integration tests requiring live services
- `make format`: Format code with ruff (imports + style)
- `make lint`: Run ruff checks + mypy type validation
- `make dev`: Start FastAPI server with hot reload on port 8000
- `make serve`: Start production server with 4 workers
- `make clean`: Remove caches, coverage reports, and generated files
- `make docker-up`: Start Neo4j, PostgreSQL, Redis via Docker Compose
- `make docker-down`: Stop all Docker services

## Coding Style & Naming Conventions
Python code uses 4-space indentation, 100-character lines, and single quotes (enforced by ruff). 
- Modules and files: `snake_case` (e.g., `graphiti_service.py`)
- Classes: `PascalCase` (e.g., `VipMemoryClient`, `APIKey`)
- Functions and variables: `snake_case` (e.g., `verify_api_key`, `created_at`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_KEY_PREFIX`)
- Pydantic models use explicit type hints with Field(...) descriptors
- Async functions prefixed with `async def`, no special naming convention
- Private attributes/methods use single underscore prefix (`_client`, `_make_request`)

Run `make format` before committing to normalize imports, quotes, and line length. Use `make lint` to catch type errors and style violations.

## Testing Guidelines
Write tests in `tests/` following the pattern `test_<module>.py`. Test classes group related tests:
- Test functions: `test_<behavior>` (e.g., `test_generate_api_key`, `test_search_memory_success`)
- Use `@pytest.mark.integration` for tests requiring database or external services
- Mock external dependencies (Graphiti client, HTTP requests) using `unittest.mock` or `pytest-mock`
- Parametrize tests with `@pytest.mark.parametrize` for multiple input scenarios
- Fixtures in `tests/fixtures.py` provide reusable test data (users, API keys, mock services)

Run `make test-unit` during development (fast feedback), `make test` before committing (full coverage check). Integration tests require Docker services: `make docker-up` then `make test-integration`.

Coverage targets:
- Overall: 50%+ (enforced in CI via `--cov-fail-under=50`)
- Core modules (auth, models, SDK client): 70%+
- View coverage report: `open htmlcov/index.html` after running `make test`

## Commit & Pull Request Guidelines
Commits use imperative mood, present tense (e.g., "Add API key authentication", "Fix memory search pagination"). Keep commits focused on single logical changes.

Before committing:
1. Run `make format` to auto-fix style issues
2. Run `make lint` to catch errors
3. Run `make test` to ensure tests pass with adequate coverage
4. Update docs if changing public APIs or configuration

Pull requests should include:
- Clear title describing the change
- Description linking to issue/ticket (if applicable)
- Notes on breaking changes, new environment variables, or database migrations
- Test coverage for new features
- Updated README/docs if user-facing behavior changes

Keep PRs focused and reasonably sized. For large refactors, break into incremental PRs that maintain functionality at each step.

## Authentication & Security
- API Key format: `vpm_sk_<64-character-hex>`
- Keys are SHA256 hashed before storage (never store plaintext)
- Default dev key auto-generated on server startup (logged to console)
- SDK clients automatically add `Authorization: Bearer <key>` header
- Web console stores keys in localStorage, adds via Axios interceptor
- Rate limiting and key rotation not yet implemented (future enhancements)

## Development Workflow
1. Clone repo and run `uv sync --extra dev` to install dependencies
2. Start backing services: `make docker-up` (Neo4j, PostgreSQL, Redis)
3. Configure environment: Copy `.env.example` to `.env`, set required variables
4. Start dev server: `make dev` (FastAPI on http://localhost:8000)
5. Run web console: `cd web && npm run dev` (Vite on http://localhost:5173)
6. Make changes, write tests, run `make format && make lint && make test`
7. Commit with clear message, push, open PR

For SDK development:
- Work in `sdk/python/vip_memory/`
- Test with `make sdk-test` 
- Build distribution: `make sdk-build`
- SDK versioning follows semantic versioning (MAJOR.MINOR.PATCH)