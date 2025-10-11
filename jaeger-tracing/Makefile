# FastAPI Jaeger Tracing Demo - Makefile
.PHONY: help install install-dev run run-dev docker-build docker-up docker-down docker-logs clean test lint format traffic demo load-test full-stop status-dev status-prod status-all test-api api-docs

# Default target
help: ## Show this help message
	@echo "FastAPI Jaeger Tracing Demo"
	@echo "==========================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
install: ## Install project dependencies using uv (for local development)
	@echo "Installing dependencies with uv..."
	uv sync

install-dev: ## Install development dependencies (for local development)
	@echo "Installing development dependencies..."
	uv sync --dev

setup: install ## Setup the project environment for local development
	@echo "Project setup complete!"
	@echo "   Run 'make run-dev' for local development"
	@echo "   Run 'make docker-dev-up' for containerized development"
	@echo "   Run 'make docker-up' for production-like setup"

dev-setup: docker-dev-build ## Quick development setup using Docker with hot reload
	@echo "Development environment ready!"
	@echo "   Run 'make docker-dev-up' to start all services"
	@echo "   Source code changes will trigger automatic reload"

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

# Docker Development Operations
docker-dev-build: ## Build Docker development images
	@echo "Building Docker development images..."
	docker-compose -f docker-compose.dev.yml build

docker-dev-up: ## Start all services in development mode with local source mounting
	@echo "Starting all services in development mode..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development services started:"
	@echo "   FastAPI Main:     http://localhost:8000 (with hot reload)"
	@echo "   User Service:     http://localhost:8001 (with hot reload)"
	@echo "   Order Service:    http://localhost:8002 (with hot reload)"
	@echo "   Payment Service:  http://localhost:8003 (with hot reload)"
	@echo "   Jaeger UI:        http://localhost:16686"
	@echo "   Redis:            localhost:6379"
	@echo "   PostgreSQL:       localhost:5432"

docker-dev-down: ## Stop development services
	@echo "Stopping development services..."
	docker-compose -f docker-compose.dev.yml down

docker-dev-logs: ## Show development logs
	@echo "Showing development logs..."
	docker-compose -f docker-compose.dev.yml logs -f

docker-dev-restart: ## Restart development services
	@echo "Restarting development services..."
	docker-compose -f docker-compose.dev.yml restart

# Docker Production Operations
docker-build: ## Build Docker production images
	@echo "Building Docker production images..."
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

# API Testing
test-api: ## Run comprehensive API endpoint tests
	@echo "Testing all API endpoints..."
	./scripts/test_api_endpoints.sh

api-docs: ## Open API documentation in browser
	@echo "API Documentation available at:"
	@echo "   Swagger UI:  http://localhost:8000/docs"
	@echo "   ReDoc:       http://localhost:8000/redoc"
	@echo "   OpenAPI:     http://localhost:8000/openapi.json"
	@echo "   Reference:   ./API_REFERENCE.md"

# Demo and Presentation
demo: ## Run full demo sequence (production-like)
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

demo-dev: ## Run development demo with hot reload
	@echo "Starting development demo sequence..."
	@echo "1. Starting development services with hot reload..."
	make docker-dev-up
	@echo "2. Waiting for services to be ready..."
	sleep 15
	@echo "3. Running demo traffic..."
	make traffic-demo
	@echo "Development demo complete! Check Jaeger UI at http://localhost:16686"
	@echo "Edit source files to see hot reload in action!"

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

status-dev: ## Show development cluster status with health checks
	@echo "Development Cluster Status:"
	@echo "============================="
	@echo "Container Status:"
	@docker-compose -f docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Health Checks:"
	@echo "FastAPI Main:     $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "DOWN")"
	@echo "User Service:     $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "DOWN")"
	@echo "Order Service:    $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null || echo "DOWN")"
	@echo "Payment Service:  $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health 2>/dev/null || echo "DOWN")"
	@echo "Jaeger UI:        $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:16686/ 2>/dev/null || echo "DOWN")"
	@echo "Redis:            $$(docker exec redis-dev redis-cli ping 2>/dev/null || echo "DOWN")"
	@echo "PostgreSQL:       $$(docker exec postgres-dev pg_isready -U demo_user -d demo_db 2>/dev/null && echo "200" || echo "DOWN")"
	@echo ""
	@echo "Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $$(docker-compose -f docker-compose.dev.yml ps -q) 2>/dev/null || echo "No containers running"

status-prod: ## Show production cluster status with health checks
	@echo "Production Cluster Status:"
	@echo "==========================="
	@echo "Container Status:"
	@docker-compose ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Health Checks:"
	@echo "FastAPI Main:     $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "DOWN")"
	@echo "User Service:     $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "DOWN")"
	@echo "Order Service:    $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null || echo "DOWN")"
	@echo "Payment Service:  $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health 2>/dev/null || echo "DOWN")"
	@echo "Jaeger UI:        $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:16686/ 2>/dev/null || echo "DOWN")"
	@echo "Kibana:           $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5601/api/status 2>/dev/null || echo "DOWN")"
	@echo "Elasticsearch:    $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/_cluster/health 2>/dev/null || echo "DOWN")"
	@echo ""
	@echo "Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $$(docker-compose ps -q) 2>/dev/null || echo "No containers running"

status-all: ## Show comprehensive status for all environments
	@echo "Comprehensive Cluster Status:"
	@echo "=============================="
	@dev_containers=$$(docker-compose -f docker-compose.dev.yml ps -q 2>/dev/null | wc -l); \
	prod_containers=$$(docker-compose ps -q 2>/dev/null | wc -l); \
	if [ $$dev_containers -gt 0 ]; then \
		echo "Development Environment:"; \
		make status-dev; \
		echo ""; \
	fi; \
	if [ $$prod_containers -gt 0 ]; then \
		echo "Production Environment:"; \
		make status-prod; \
	fi; \
	if [ $$dev_containers -eq 0 ] && [ $$prod_containers -eq 0 ]; then \
		echo "No active environments found."; \
		echo "Run 'make docker-dev-up' for development or 'make docker-up' for production."; \
	fi

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
# Note: dev-setup is defined earlier in the file for Docker development

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