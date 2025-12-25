.PHONY: install test format lint clean dev serve help web-install web-dev web-build web-preview web-test web-test-coverage web-lint web-e2e test-data get-api-key

help:
	@echo "MemStack Development Commands"
	@echo "================================"
	@echo "install     - Install all dependencies (dev + production)"
	@echo "test        - Run all tests with coverage"
	@echo "test-unit   - Run unit tests only"
	@echo "test-integration - Run integration tests only"
	@echo "format      - Format code with ruff"
	@echo "lint        - Run linting checks (ruff + mypy)"
	@echo "clean       - Remove generated files and caches"
	@echo "dev         - Start development server with hot reload"
	@echo "serve       - Start production server"
	@echo "docker-up   - Start all services with Docker Compose"
	@echo "docker-dev  - Start infrastructure services only (Neo4j, Postgres, Redis)"
	@echo "docker-down - Stop all Docker services"
	@echo ""
	@echo "API & Test Data:"
	@echo "get-api-key - Get or show how to obtain API key"
	@echo "test-data   - Generate test data (default: 50 random episodes)"
	@echo "test-data-user - Generate user activity series"
	@echo "test-data-collab - Generate project collaboration data"
	@echo ""
	@echo "Web Commands:"
	@echo "web-install - Install web dependencies"
	@echo "web-dev     - Start web development server"
	@echo "web-build   - Build web for production"
	@echo "web-preview - Preview web build"
	@echo "web-test    - Run web tests"
	@echo "web-test-coverage - Run web tests with coverage"
	@echo "web-lint    - Run web linting"
	@echo "web-e2e     - Run web e2e tests (Playwright)"

install:
	pip install -e ".[dev,neo4j,evaluation]"

test:
	uv run pytest tests/ --cov=server --cov=sdk/python/memstack --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-unit:
	uv run pytest tests/ -m "not integration" --cov=server --cov=sdk/python/memstack --cov-report=term-missing

test-integration:
	uv run pytest tests/ -m "integration" -v

format:
	uv run ruff check --fix server/ sdk/ tests/
	uv run ruff format server/ sdk/ tests/

lint:
	uv run ruff check server/ sdk/ tests/
	uv run mypy server/
clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev:
	uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

serve:
	uv run uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4

docker-up:
	docker-compose up -d

docker-dev:
	docker-compose up -d neo4j postgres redis

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# SDK specific commands
sdk-install:
	cd sdk/python && pip install -e ".[dev]"

sdk-test:
	pytest sdk/python/tests/ --cov=sdk/python/memstack --cov-report=term-missing

sdk-build:
	cd sdk/python && python -m build

# Database commands
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-revision:
	alembic revision --autogenerate -m "$(message)"

# Web commands
web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-preview:
	cd web && npm run preview

web-test:
	cd web && npm test

web-test-coverage:
	cd web && npm run test:coverage

web-lint:
	cd web && npm run lint

web-e2e:
	cd web && npm run test:e2e

# API Key helper
get-api-key:
	@./scripts/get_api_key.sh

# Test data generation commands
COUNT?=50
USER_NAME?="Alice Johnson"
PROJECT_NAME?="Alpha Research"
DAYS?=7

test-data:
	uv run python scripts/generate_test_data.py --count $(COUNT) --mode random

test-data-user:
	uv run python scripts/generate_test_data.py --mode user-series --user-name "$(USER_NAME)" --days $(DAYS)

test-data-collab:
	uv run python scripts/generate_test_data.py --mode collaboration --project-name "$(PROJECT_NAME)" --days $(DAYS)
