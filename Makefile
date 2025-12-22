.PHONY: install test format lint clean dev serve help web-install web-dev web-build

help:
	@echo "vip-memory Development Commands"
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
	@echo "docker-down - Stop all Docker services"
	@echo ""
	@echo "Web Commands:"
	@echo "web-install - Install web dependencies"
	@echo "web-dev     - Start web development server"
	@echo "web-build   - Build web for production"

install:
	pip install -e ".[dev,neo4j,evaluation]"

test:
	uv run pytest tests/ --cov=server --cov=sdk/python/vip_memory --cov-report=html --cov-report=term-missing --cov-fail-under=50

test-unit:
	uv run pytest tests/ -m "not integration" --cov=server --cov=sdk/python/vip_memory --cov-report=term-missing

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

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# SDK specific commands
sdk-install:
	cd sdk/python && pip install -e ".[dev]"

sdk-test:
	pytest sdk/python/tests/ --cov=sdk/python/vip_memory --cov-report=term-missing

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
