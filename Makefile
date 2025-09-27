# Paperclip Development Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev test lint format clean build run docker-build docker-up docker-down

# Default target
help:
	@echo "Paperclip Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install     Install dependencies and setup development environment"
	@echo "  setup-env   Create .env file from template"
	@echo ""
	@echo "Development:"
	@echo "  dev         Start development servers (API + UI)"
	@echo "  api         Start API server only"
	@echo "  ui          Start UI server only"
	@echo "  worker      Start background worker"
	@echo ""
	@echo "Code Quality:"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  type-check  Run mypy type checking"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    Build Docker images"
	@echo "  docker-up       Start all services with Docker Compose"
	@echo "  docker-down     Stop all Docker services"
	@echo "  docker-logs     View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean up temporary files and caches"
	@echo "  reset       Reset development environment"

# Installation and setup
install:
	pip install -e ".[dev,ui,all]"
	pre-commit install

setup-env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from template"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Development servers
dev:
	@echo "Starting Paperclip development servers..."
	@trap 'kill %1; kill %2' INT; \
	make api & \
	make ui & \
	wait

api:
	@echo "Starting API server..."
	python -m api.main

ui:
	@echo "Starting UI server..."
	streamlit run ui/main.py --server.port=8501

worker:
	@echo "Starting background worker..."
	python -m celery worker -A worker.celery --loglevel=info

# Testing
test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-coverage:
	pytest --cov=paperclip --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 .
	black --check .
	isort --check-only .

format:
	black .
	isort .

type-check:
	mypy .

# Docker commands
docker-build:
	docker-compose build

docker-up:
	@echo "Starting Paperclip with Docker Compose..."
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-reset:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

# Database commands
db-migrate:
	@echo "Running database migrations..."
	python -m scripts.migrate

db-reset:
	@echo "Resetting database..."
	python -m scripts.reset_db

# Utilities
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

reset: clean
	rm -rf uploads/
	rm -rf output/
	rm -rf temp/
	rm -rf logs/
	mkdir -p uploads output temp logs

# Production deployment
build:
	python -m build

deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-production:
	@echo "Deploying to production..."
	# Add production deployment commands here

# Documentation
docs:
	@echo "Building documentation..."
	# Add documentation build commands

docs-serve:
	@echo "Serving documentation..."
	# Add documentation serve commands

# Health checks
health-check:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health/ || echo "API not responding"
	curl -f http://localhost:8501/healthz || echo "UI not responding"

# Environment info
info:
	@echo "Paperclip Environment Information"
	@echo "================================"
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Git commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'Not a git repository')"
	@echo ""
	@echo "Environment variables:"
	@echo "ENVIRONMENT=$${ENVIRONMENT:-not set}"
	@echo "DEBUG=$${DEBUG:-not set}"
	@echo "API_PORT=$${API_PORT:-not set}"
	@echo "UI_PORT=$${UI_PORT:-not set}"
