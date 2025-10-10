# FastAPI Jaeger Tracing Demo - Makefile
.PHONY: help install install-dev run run-dev docker-build docker-up docker-down docker-logs clean test lint format traffic demo load-test full-stop

# Default target
help: ## Show this help message
	@echo "FastAPI Jaeger Tracing Demo"
	@echo "==========================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
install: ## Install project dependencies using uv
	@echo "Installing dependencies with uv..."
	uv sync

install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	uv sync --dev

setup: install ## Setup the project environment
	@echo "Project setup complete!"
	@echo "   Run 'make run-dev' to start development"
	@echo "   Run 'make docker-up' to start with Docker"

# Local Development
run: ## Run FastAPI application locally
	@echo "Starting FastAPI application..."
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev: ## Run FastAPI application in development mode with hot reload
	@echo "Starting FastAPI application in development mode..."
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-jaeger: ## Start only Jaeger using Docker Compose
	@echo "Starting Jaeger..."
	docker-compose -f docker-compose.dev.yml up -d jaeger
	@echo "Jaeger UI available at: http://localhost:16686"

# Docker Operations
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build

docker-up: ## Start all services with Docker Compose
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d
	@echo "Services started:"
	@echo "   FastAPI Main:     http://localhost:8000"
	@echo "   User Service:     http://localhost:8001" 
	@echo "   Order Service:    http://localhost:8002"
	@echo "   Payment Service:  http://localhost:8003"
	@echo "   Jaeger UI:        http://localhost:16686"

docker-up-dev: ## Start development services with Docker Compose
	@echo "Starting development services..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development services started:"
	@echo "   Jaeger UI:        http://localhost:16686"
	@echo "   Redis:            localhost:6379"
	@echo "   PostgreSQL:       localhost:5432"

docker-down: ## Stop all Docker services
	@echo "Stopping Docker services..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

docker-logs: ## Show Docker logs
	@echo "Docker logs:"
	docker-compose logs -f

docker-clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

# Code Quality
lint: ## Run linting with ruff
	@echo "Running linting..."
	uv run ruff check .

format: ## Format code with black and ruff
	@echo "Formatting code..."
	uv run black .
	uv run ruff format .

type-check: ## Run type checking with mypy
	@echo "Running type checking..."
	uv run mypy app/ config/

test: ## Run tests
	@echo "Running tests..."
	uv run pytest tests/ -v

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=app --cov=config --cov-report=html --cov-report=term

# Traffic Generation and Testing
traffic: ## Generate sample traffic (60 seconds)
	@echo "Generating sample traffic..."
	uv run python scripts/generate_traffic.py --mode activity --duration 60

traffic-demo: ## Run demo traffic scenarios
	@echo "Running demo traffic scenarios..."
	uv run python scripts/generate_traffic.py --mode demo

traffic-stress: ## Run stress test traffic
	@echo "Running stress test traffic..."
	uv run python scripts/generate_traffic.py --mode stress --rps 20 --duration 30

load-test: ## Run comprehensive load test
	@echo "Running load test..."
	uv run python scripts/load_test.py --users 10 --requests 50 --ramp-up 10

load-test-heavy: ## Run heavy load test
	@echo "Running heavy load test..."
	uv run python scripts/load_test.py --users 25 --requests 100 --ramp-up 15

# Demo and Presentation
demo: ## Run full demo sequence
	@echo "Starting demo sequence..."
	@echo "1. Starting services..."
	make docker-up
	@echo "2. Waiting for services to be ready..."
	sleep 10
	@echo "3. Running demo traffic..."
	make traffic-demo
	@echo "4. Running load test..."
	make load-test
	@echo "Demo complete! Check Jaeger UI at http://localhost:16686"

demo-clean: ## Clean demo and restart
	@echo "Cleaning demo environment..."
	make docker-down
	make docker-clean
	make demo

# Health Checks
health: ## Check service health
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "[ERROR] Main service not available"
	@curl -f http://localhost:8001/health || echo "[ERROR] User service not available"
	@curl -f http://localhost:8002/health || echo "[ERROR] Order service not available"
	@curl -f http://localhost:8003/health || echo "[ERROR] Payment service not available"
	@curl -f http://localhost:16686/ || echo "[ERROR] Jaeger UI not available"

status: ## Show service status
	@echo "Service Status:"
	@echo "=================="
	@docker-compose ps

# Cleanup
clean: ## Clean up temporary files and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# Quick Development Workflows
dev-setup: ## Quick development setup
	make install-dev
	make run-jaeger
	@echo "Development environment ready!"
	@echo "   Run 'make run-dev' to start the application"

full-setup: ## Full setup with all services
	make install-dev
	make docker-up
	@echo "Full environment ready!"

full-stop: ## Stop all services and processes completely
	@echo "Stopping all services and processes..."
	@echo "1. Stopping Docker services..."
	-docker-compose down 2>/dev/null
	-docker-compose -f docker-compose.dev.yml down 2>/dev/null
	@echo "2. Killing local FastAPI processes..."
	-pkill -f "uvicorn.*app.main:app" 2>/dev/null
	-pkill -f "python.*app/main.py" 2>/dev/null
	-pkill -f "python.*-m.*uvicorn.*app.main:app" 2>/dev/null
	@echo "3. Stopping traffic generation processes..."
	-pkill -f "generate_traffic.py" 2>/dev/null
	-pkill -f "load_test.py" 2>/dev/null
	@echo "4. Cleaning up any remaining processes..."
	-pkill -f "fastapi-jaeger-tracing" 2>/dev/null
	@echo "All services stopped!"

# Monitoring and Debugging
logs-app: ## Show application logs
	docker-compose logs -f fastapi-main

logs-jaeger: ## Show Jaeger logs  
	docker-compose logs -f jaeger

shell-app: ## Open shell in main application container
	docker-compose exec fastapi-main /bin/bash

# Environment info
env-info: ## Show environment information
	@echo "Environment Information:"
	@echo "=========================="
	@echo "Python version: $(shell python --version 2>/dev/null || echo 'Not available')"
	@echo "UV version: $(shell uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker version: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose version: $(shell docker-compose --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "Project structure:"
	@tree -L 2 -I '__pycache__|*.pyc|.git' . 2>/dev/null || ls -la