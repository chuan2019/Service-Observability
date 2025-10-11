# FastAPI Jaeger Tracing Demo - Makefile
.PHONY: help run run-dev docker-build docker-down docker-logs clean test lint format traffic demo load-test full-stop status-dev status-prod status-all test-api api-docs

# Default target
help: ## Show this help message
	@echo "FastAPI Jaeger Tracing Demo"
	@echo "==========================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Local Development (only used for local application development)
run: ## Run FastAPI application locally
	@echo "Installing dependencies with uv..."
	uv sync
	@echo "Starting FastAPI application..."
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev: ## Run FastAPI application in development mode with hot reload
	@echo "Installing development dependencies..."
	uv sync --dev
	@echo "Starting FastAPI application in development mode..."
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-jaeger: ## Start only Jaeger using Docker Compose
	@echo "Starting Jaeger..."
	docker-compose -f docker-compose.dev.yml up -d jaeger
	@echo "Jaeger UI available at: http://localhost:16686"

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
	@echo "Testing all API endpoints..."
	./scripts/test_api_endpoints.sh

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
api-docs: ## Open API documentation in browser
	@echo "API Documentation available at:"
	@echo "   Swagger UI:  http://localhost:8000/docs"
	@echo "   ReDoc:       http://localhost:8000/redoc"
	@echo "   OpenAPI:     http://localhost:8000/openapi.json"
	@echo "   Reference:   ./API_REFERENCE.md"

# Demo and Presentation
setup-prod: ## Run full demo sequence (production-like)
	@echo "Starting demo sequence..."
	@echo "1. Starting services..."
	docker-compose up -d --build
	@echo "2. Waiting for services to be ready..."
	sleep 10
	@echo "3. Running demo traffic..."
	make traffic-demo
	@echo "4. Running load test..."
	make load-test
	@echo "Demo complete! Check Jaeger UI at http://localhost:16686"

setup-dev: ## Run development demo with hot reload
	@echo "Starting development demo sequence..."
	@echo "1. Starting development services with hot reload..."
	docker-compose -f docker-compose.dev.yml up -d --build
	@echo "2. Waiting for services to be ready..."
	sleep 15
	@echo "3. Running demo traffic..."
	make traffic-demo
	@echo "Development demo complete! Check Jaeger UI at http://localhost:16686"
	@echo "Edit source files to see hot reload in action!"

stop-prod: ## stop and clean production demo 
	@echo "Stopping and Cleaning production environment..."
	docker-compose down
	docker-compose down -v --remove-orphans
	docker system prune -f

stop-dev: ## stop and clean development demo
	@echo "Stopping and Cleaning development environment..."
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

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

# Cleanup
clean: ## Clean up temporary files and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# Monitoring and Debugging
logs-dev: ## Show development logs
	@echo "Showing development logs..."
	docker-compose -f docker-compose.dev.yml logs -f

logs-prod: ## Show production logs
	@echo "Showing production logs..."
	docker-compose logs -f

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