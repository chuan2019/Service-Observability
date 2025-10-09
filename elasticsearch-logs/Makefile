# FastAPI Elasticsearch Logging Demo
# Makefile for development and deployment tasks

.PHONY: help install dev-install clean test lint format run docker-up docker-down docker-logs kibana-setup full-setup full-stop

# Default target
help:
	@echo "Available commands:"
	@echo "  install       - Install production dependencies using uv"
	@echo "  dev-install   - Install development dependencies using uv"
	@echo "  clean         - Clean up cache files and temporary directories"
	@echo "  test          - Run all tests with coverage (FastAPI auto-managed)"
	@echo "  test-unit     - Run unit tests only (FastAPI auto-managed)"
	@echo "  test-integration - Run integration tests only (FastAPI auto-managed)"
	@echo "  test-quick    - Run quick tests without coverage"
	@echo "  test-manual   - Run manual logging tests (requires running services)"
	@echo "  test-report   - Generate test coverage report"
	@echo "  test-services - Check if all services are running"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code with black and isort"
	@echo "  run           - Run FastAPI application locally"
	@echo "  docker-up     - Start Elasticsearch and Kibana with Docker"
	@echo "  docker-down   - Stop Docker containers"
	@echo "  docker-logs   - Show Docker container logs"
	@echo "  kibana-setup  - Setup Kibana index patterns and dashboards"
	@echo "  full-setup    - Complete setup (docker + install + kibana)"
	@echo "  full-stop     - Stop all services (Docker containers)"

# Installation
install:
	@echo "Installing production dependencies..."
	uv sync --no-dev

dev-install:
	@echo "Installing development dependencies..."
	uv sync

# Cleanup
clean:
	@echo "Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Testing
test:
	@echo "Running all tests with coverage..."
	uv run pytest tests/ -v --cov=app --cov-report=term --cov-report=html

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/test_api.py tests/test_logging.py -v

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/test_integration.py -v -m integration

test-manual:
	@echo "Running manual logging tests..."
	./scripts/run-tests.sh manual

test-report:
	@echo "Generating test coverage report..."
	uv run pytest tests/ --cov=app --cov-report=html --cov-report=term

test-services:
	@echo "Checking if services are running..."
	./scripts/run-tests.sh services

test-quick:
	@echo "Running quick tests (no coverage)..."
	uv run pytest tests/ -v --tb=short

# Code quality
lint:
	@echo "Running linting checks..."
	uv run ruff check .
	uv run mypy .

format:
	@echo "Formatting code..."
	uv run black .
	uv run isort .
	uv run ruff check --fix .

# Development
run:
	@echo "Starting FastAPI application..."
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Docker operations
docker-up:
	@echo "Starting Elasticsearch and Kibana..."
	docker-compose up -d elasticsearch kibana
	@echo "Waiting for services to be ready..."
	@echo "Elasticsearch will be available at: http://localhost:9200"
	@echo "Kibana will be available at: http://localhost:5601"

docker-up-all:
	@echo "Starting all services including FastAPI..."
	docker-compose --profile production up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Showing Docker container logs..."
	docker-compose logs -f

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f

# Kibana setup
kibana-setup:
	@echo "Setting up Kibana index patterns..."
	./scripts/setup-kibana.sh

# Complete setup
full-setup: docker-up dev-install
	@echo "Waiting for Elasticsearch to be ready..."
	sleep 30
	@echo "Setting up Kibana..."
	make kibana-setup
	@echo "Setup complete!"
	@echo ""
	@echo "Services available at:"
	@echo "  - Elasticsearch: http://localhost:9200"
	@echo "  - Kibana: http://localhost:5601"
	@echo ""
	@echo "To start the FastAPI app: make run"

# Stop everything
full-stop:
	@echo "Stopping all services..."
	@echo "Note: If FastAPI is running, stop it with Ctrl+C"
	make docker-down
	@echo "All Docker services stopped!"
	@echo ""
	@echo "To completely clean up (including volumes): make docker-clean"

# Health checks
health-check:
	@echo "Checking service health..."
	@curl -f http://localhost:9200/_cluster/health || echo "Elasticsearch not ready"
	@curl -f http://localhost:5601/api/status || echo "Kibana not ready"
	@curl -f http://localhost:8000/health || echo "FastAPI not running"

# Development workflow
dev: docker-up dev-install
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the FastAPI application"