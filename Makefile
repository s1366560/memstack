# =============================================================================
# MemStack - Enterprise AI Memory Cloud Platform
# =============================================================================
# A comprehensive Makefile for managing the MemStack project including
# backend services, web frontend, SDK, testing, and development tools.
#
# Project Structure:
#   - src/          : Hexagonal architecture backend (Python)
#   - web/          : React frontend (TypeScript/Vite)
#   - tests/        : Integration tests
#   - src/tests/    : Unit & integration tests (new structure)
#   - sdk/python/   : Python SDK
# =============================================================================

.PHONY: help install update clean

# =============================================================================
# Default Target
# =============================================================================

help: ## Show this help message
	@echo "MemStack Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install all dependencies (backend + web)"
	@echo "  make install-backend  - Install backend dependencies only"
	@echo "  make install-web      - Install web dependencies only"
	@echo "  make update           - Update all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start all backend services (API + worker + infra)"
	@echo "  make dev-stop         - Stop all background services"
	@echo "  make dev-logs         - View all service logs"
	@echo "  make dev-backend      - Start API server only (foreground)"
	@echo "  make dev-worker       - Start worker service only (foreground)"
	@echo "  make dev-web          - Start web development server"
	@echo "  make dev-infra        - Start infrastructure services (Neo4j, Postgres, Redis)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-web         - Run web tests"
	@echo "  make test-e2e         - Run end-to-end tests (Playwright)"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           - Format all code (Python + TypeScript)"
	@echo "  make format-backend   - Format Python code with ruff"
	@echo "  make format-web       - Format TypeScript code"
	@echo "  make lint             - Lint all code"
	@echo "  make lint-backend     - Lint Python code (ruff + mypy)"
	@echo "  make lint-web         - Lint TypeScript code"
	@echo "  make type-check       - Type check all code"
	@echo "  make check            - Run all quality checks (format + lint + test)"
	@echo ""
	@echo "Database:"
	@echo "  make db-init          - Initialize database (create if not exists)"
	@echo "  make db-reset         - Reset database (WARNING: deletes all data)"
	@echo "  make db-shell         - Open PostgreSQL shell"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Start all Docker services"
	@echo "  make docker-down      - Stop all Docker services"
	@echo "  make docker-logs      - Show Docker service logs"
	@echo "  make docker-build     - Build Docker images"
	@echo ""
	@echo "Production:"
	@echo "  make build            - Build all for production"
	@echo "  make build-backend    - Build backend"
	@echo "  make build-web        - Build web frontend"
	@echo "  make serve            - Start production server"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Remove all generated files and caches"
	@echo "  make clean-backend    - Clean backend build artifacts"
	@echo "  make clean-web        - Clean web build artifacts"
	@echo "  make clean-logs       - Clean log files"
	@echo "  make shell            - Open Python shell in project environment"
	@echo "  make get-api-key      - Show API key information"
	@echo "  make test-data        - Generate test data (default: 50 episodes)"
	@echo ""
	@echo "Use 'make help' to show this message"

# =============================================================================
# Setup & Installation
# =============================================================================

install: install-backend install-web ## Install all dependencies
	@echo "✅ All dependencies installed"

install-backend: ## Install backend Python dependencies
	@echo "📦 Installing backend dependencies..."
	uv sync --extra dev --extra neo4j --extra evaluation
	@echo "✅ Backend dependencies installed"

install-web: ## Install web frontend dependencies
	@echo "📦 Installing web dependencies..."
	cd web && pnpm install
	@echo "✅ Web dependencies installed"

update: ## Update all dependencies
	@echo "📦 Updating dependencies..."
	uv lock --upgrade
	cd web && pnpm update
	@echo "✅ Dependencies updated"

# =============================================================================
# Development
# =============================================================================

dev: dev-all ## Start all backend services (API + worker + infra)
	@echo "🚀 Starting full development environment..."

dev-all: dev-infra db-init
	@echo "🚀 Starting API server and worker in background..."
	@echo "   API: http://localhost:8000 (logs: logs/api.log)"
	@echo "   Worker: running in background (logs: logs/worker.log)"
	@mkdir -p logs
	@uv run uvicorn src.infrastructure.adapters.primary.web.main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
	@echo "$$!" > logs/api.pid
	@uv run python src/worker.py > logs/worker.log 2>&1 &
	@echo "$$!" > logs/worker.pid
	@sleep 2
	@echo "✅ Services started!"
	@echo ""
	@echo "View logs with:"
	@echo "  tail -f logs/api.log    # API server logs"
	@echo "  tail -f logs/worker.log # Worker logs"
	@echo ""
	@echo "Stop services with:"
	@echo "  make dev-stop"

dev-stop: ## Stop all background services
	@echo "🛑 Stopping background services..."
	@if [ -f logs/api.pid ]; then kill $$(cat logs/api.pid) 2>/dev/null || true; rm logs/api.pid; echo "✅ API stopped"; fi
	@if [ -f logs/worker.pid ]; then kill $$(cat logs/worker.pid) 2>/dev/null || true; rm logs/worker.pid; echo "✅ Worker stopped"; fi
	@echo "✅ All services stopped"

dev-logs: ## Show all service logs (follow mode)
	@echo "📋 Showing logs (Ctrl+C to exit)..."
	@tail -f logs/api.log logs/worker.log

dev-backend: ## Start backend development server with hot reload (API only, foreground)
	@echo "🚀 Starting backend API server..."
	uv run uvicorn src.infrastructure.adapters.primary.web.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Start worker service only (foreground)
	@echo "🔧 Starting worker service..."
	uv run python src/worker.py

dev-web: ## Start web development server
	@echo "🚀 Starting web development server..."
	cd web && pnpm run dev

dev-infra: ## Start infrastructure services only
	@echo "🚀 Starting infrastructure services..."
	docker-compose up -d neo4j postgres redis
	@echo "✅ Infrastructure services started"
	@echo "   Neo4j: http://localhost:7474"
	@echo "   Postgres: localhost:5433"
	@echo "   Redis: localhost:6380"

# =============================================================================
# Testing
# =============================================================================

test: test-backend test-web ## Run all tests
	@echo "✅ All tests completed"

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	uv run pytest tests/ src/tests/ -v --tb=short

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	uv run pytest tests/ src/tests/ -m "not integration" -v --tb=short

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	uv run pytest tests/ src/tests/ -m "integration" -v --tb=short

test-web: ## Run web tests
	@echo "🧪 Running web tests..."
	cd web && pnpm run test

test-e2e: ## Run end-to-end tests (requires services running)
	@echo "🧪 Running E2E tests..."
	cd web && pnpm run test:e2e

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ src/tests/ --cov=src --cov=tests --cov-report=html --cov-report=term-missing --cov-fail-under=80
	@echo "📊 Coverage report generated: htmlcov/index.html"

test-watch: ## Run tests in watch mode
	@echo "🧪 Running tests in watch mode..."
	uv run pytest tests/ src/tests/ -f

# =============================================================================
# Code Quality
# =============================================================================

format: format-backend format-web ## Format all code
	@echo "✅ All code formatted"

format-backend: ## Format Python code
	@echo "🎨 Formatting Python code..."
	uv run ruff check --fix src/ tests/ sdk/
	uv run ruff format src/ tests/ sdk/
	@echo "✅ Python code formatted"

format-web: ## Format TypeScript code
	@echo "🎨 Formatting TypeScript code..."
	cd web && pnpm run lint --fix
	@echo "✅ TypeScript code formatted"

lint: lint-backend lint-web ## Lint all code
	@echo "✅ All code linted"

lint-backend: ## Lint Python code
	@echo "🔍 Linting Python code..."
	uv run ruff check src/ tests/ sdk/
	uv run mypy src/ --ignore-missing-imports
	@echo "✅ Python code linted"

lint-web: ## Lint TypeScript code
	@echo "🔍 Linting TypeScript code..."
	cd web && pnpm run lint
	cd web && pnpm run type-check
	@echo "✅ TypeScript code linted"

type-check: lint-backend ## Type check all code (alias for lint-backend)

check: format lint test ## Run all quality checks
	@echo "✅ All quality checks passed"

# =============================================================================
# Database
# =============================================================================

db-init: ## Initialize database (create if not exists)
	@echo "🗄️  Initializing database..."
	@if docker-compose exec -T postgres psql -U postgres -lqt | grep -q vip_memory; then \
		echo "✓ Database 'vip_memory' already exists"; \
	else \
		echo "Creating database 'vip_memory'..."; \
		docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE vip_memory;"; \
		echo "✓ Database created"; \
	fi
	@echo "✅ Database ready (tables will be auto-created on first startup)"

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS vip_memory;"; \
		docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE vip_memory;"; \
		echo "✅ Database reset completed"; \
	else \
		echo "❌ Aborted"; \
	fi

db-shell: ## Open PostgreSQL shell
	@echo "🐚 Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U postgres vip_memory

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start all Docker services
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started"
	@echo "   API: http://localhost:8000"
	@echo "   Web: http://localhost:3000"
	@echo "   Neo4j: http://localhost:7474"
	@docker-compose ps

docker-down: ## Stop all Docker services
	@echo "🐳 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped"

docker-logs: ## Show Docker service logs
	docker-compose logs -f

docker-build: ## Build Docker images
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

docker-restart: docker-down docker-up ## Restart Docker services

# =============================================================================
# Production
# =============================================================================

build: build-backend build-web ## Build all for production
	@echo "✅ Build completed"

build-backend: ## Build backend for production
	@echo "🏗️  Building backend..."
	@echo "✅ Backend built"

build-web: ## Build web frontend for production
	@echo "🏗️  Building web frontend..."
	cd web && pnpm run build
	@echo "✅ Web frontend built"

serve: ## Start production server
	@echo "🚀 Starting production server..."
	uv run uvicorn src.infrastructure.adapters.primary.web.main:app --host 0.0.0.0 --port 8000 --workers 4

# =============================================================================
# Utilities
# =============================================================================

clean: clean-backend clean-web ## Remove all generated files and caches
	@echo "✅ All cleaned up"

clean-backend: ## Clean backend build artifacts
	@echo "🧹 Cleaning backend artifacts..."
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Backend artifacts cleaned"

clean-web: ## Clean web build artifacts
	@echo "🧹 Cleaning web artifacts..."
	cd web && rm -rf node_modules/.vite
	cd web && rm -rf dist
	@echo "✅ Web artifacts cleaned"

clean-logs: ## Clean log files
	@echo "🧹 Cleaning logs..."
	rm -rf logs
	@echo "✅ Logs cleaned"

shell: ## Open Python shell in project environment
	@echo "🐚 Opening Python shell..."
	uv run python

shell-ipython: ## Open IPython shell in project environment
	@echo "🐚 Opening IPython shell..."
	uv run ipython

get-api-key: ## Show API key information
	@echo "🔑 API Key Information:"
	@echo ""
	@echo "To get an API key, you need to:"
	@echo "1. Start the dev server: make dev"
	@echo "2. Register a user at http://localhost:8000/docs#/auth/register"
	@echo "3. Login at http://localhost:8000/docs#/auth/login"
	@echo "4. Copy the access_token from the response"
	@echo ""
	@echo "Then use it in your requests:"
	@echo "  Authorization: Bearer <your-token>"

# =============================================================================
# Test Data Generation
# =============================================================================

COUNT?=50
USER_NAME?="Alice Johnson"
PROJECT_NAME?="Alpha Research"
DAYS?=7

test-data: ## Generate test data (default: 50 random episodes)
	@echo "📊 Generating test data..."
	uv run python scripts/generate_test_data.py --count $(COUNT) --mode random
	@echo "✅ Test data generated"

test-data-user: ## Generate user activity series
	@echo "📊 Generating user activity data..."
	uv run python scripts/generate_test_data.py --mode user-series --user-name "$(USER_NAME)" --days $(DAYS)
	@echo "✅ User activity data generated"

test-data-collab: ## Generate project collaboration data
	@echo "📊 Generating collaboration data..."
	uv run python scripts/generate_test_data.py --mode collaboration --project-name "$(PROJECT_NAME)" --days $(DAYS)
	@echo "✅ Collaboration data generated"

# =============================================================================
# SDK Commands
# =============================================================================

sdk-install: ## Install SDK in development mode
	@echo "📦 Installing SDK..."
	cd sdk/python && pip install -e ".[dev]"
	@echo "✅ SDK installed"

sdk-test: ## Run SDK tests
	@echo "🧪 Testing SDK..."
	cd sdk/python && pytest tests/ --cov=memstack --cov-report=term-missing
	@echo "✅ SDK tests completed"

sdk-build: ## Build SDK package
	@echo "🏗️  Building SDK..."
	cd sdk/python && python -m build
	@echo "✅ SDK built"

# =============================================================================
# CI/CD Support
# =============================================================================

ci-install: install ## Install dependencies for CI
	@echo "✅ CI dependencies installed"

ci-lint: lint ## Run linting for CI
	@echo "✅ CI linting passed"

ci-test: test ## Run tests for CI
	@echo "✅ CI tests passed"

ci-build: build ## Build for CI
	@echo "✅ CI build completed"

ci: ci-lint ci-test ci-build ## Run complete CI pipeline
	@echo "✅ CI pipeline completed successfully"

# =============================================================================
# Miscellaneous
# =============================================================================

.DEFAULT_GOAL := help
