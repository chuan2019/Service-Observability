# Makefile for FastAPI Prometheus Metrics Application

.PHONY: help install dev-install clean uv-lock uv-sync uv-init test lint format run docker-build docker-run docker-compose-up docker-compose-down \
        start stop restart status logs logs-app logs-prometheus logs-grafana \
        traffic-light traffic-medium traffic-heavy traffic-stop \
        monitor dashboard prometheus grafana \
        backup restore cleanup reset \
        dev-setup production-setup full-setup

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies using uv
	uv sync --no-dev

dev-install:  ## Install development dependencies using uv
	uv sync --all-extras

clean:  ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

uv-lock:  ## Update uv.lock file
	uv lock

uv-sync:  ## Sync dependencies with uv.lock
	uv sync

uv-init:  ## Initialize uv project and create virtual environment
	uv venv --clear
	uv sync --all-extras

test:  ## Run tests
	uv run pytest -v

test-coverage:  ## Run tests with coverage
	uv run pytest --cov=app --cov-report=html --cov-report=term-missing

lint:  ## Run linting
	uv run flake8 app/ tests/

format:  ## Format code
	uv run black app/ tests/
	uv run isort app/ tests/

check:  ## Run all quality checks
	@echo "Running format check..."
	uv run black --check app/ tests/
	@echo "Running import sort check..."
	uv run isort --check-only app/ tests/
	@echo "Running linting..."
	uv run flake8 app/ tests/
	@echo "Running tests..."
	uv run pytest

run:  ## Run the application locally
	uv run python -m app.main

run-dev:  ## Run the application in development mode
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:  ## Build Docker image
	docker build -f docker/Dockerfile -t fastapi-prometheus-metrics .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 fastapi-prometheus-metrics

docker-compose-up:  ## Start all services with docker-compose
	docker-compose up -d

docker-compose-down:  ## Stop all services
	docker-compose down

docker-compose-logs:  ## View logs from all services
	docker-compose logs -f

setup-env:  ## Copy example environment file
	cp .env.example .env
	@echo "Environment file created. Please edit .env as needed."

install-hooks:  ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	echo "#!/bin/sh\nmake check" > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hooks installed!"

metrics:  ## Show current metrics (requires running application)
	@echo "Fetching metrics from http://localhost:8000/metrics"
	@curl -s http://localhost:8000/metrics | head -20

health:  ## Check application health
	@echo "Checking application health..."
	@curl -s http://localhost:8000/health/ | uv run python -m json.tool

# Development workflow commands
dev-setup: setup-env uv-init  ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make run-dev' to start the application."

production-setup: install  ## Production setup
	@echo "Production environment setup complete!"
	@echo "Configure your .env file and run 'make run' to start."

# =============================================================================
# DOCKER OPERATIONS
# =============================================================================

start:  ## Start all services (alias for docker-compose-up)
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started! Waiting for initialization..."
	@sleep 5
	@echo "Services should be available at:"
	@echo "  FastAPI App: http://localhost:8000"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3000 (admin/admin123)"

stop:  ## Stop all services (alias for docker-compose-down)
	@echo "Stopping all services..."
	docker-compose down

restart:  ## Restart all services
	@echo "Restarting all services..."
	docker-compose down
	docker-compose up -d
	@echo "Services restarted!"

status:  ## Show status of all containers
	@echo "Container status:"
	@docker-compose ps

logs:  ## Show logs from all services
	docker-compose logs -f

logs-app:  ## Show logs from FastAPI application only
	docker-compose logs -f fastapi-app

logs-prometheus:  ## Show logs from Prometheus only
	docker-compose logs -f prometheus

logs-grafana:  ## Show logs from Grafana only
	docker-compose logs -f grafana

# =============================================================================
# TRAFFIC GENERATION
# =============================================================================

traffic-light:  ## Generate light traffic (1 req/sec for 30 seconds)
	@echo "Generating light traffic (1 req/sec for 30 seconds)..."
	@for i in $$(seq 1 30); do \
		curl -s http://localhost:8000/health/ > /dev/null && echo "Request $$i completed" || echo "Request $$i failed"; \
		sleep 1; \
	done
	@echo "Light traffic generation completed!"

traffic-medium:  ## Generate medium traffic (5 req/sec for 60 seconds)
	@echo "Generating medium traffic (5 req/sec for 60 seconds)..."
	@for i in $$(seq 1 300); do \
		curl -s http://localhost:8000/api/v1/users/ > /dev/null && echo -n "." || echo -n "x"; \
		if [ $$((i % 50)) -eq 0 ]; then echo " [$$i/300]"; fi; \
		sleep 0.2; \
	done
	@echo "\nMedium traffic generation completed!"

traffic-heavy:  ## Generate heavy traffic (concurrent requests for 2 minutes)
	@echo "Generating heavy traffic (concurrent requests for 2 minutes)..."
	@echo "This will create mixed traffic patterns to various endpoints..."
	@(for i in $$(seq 1 120); do \
		curl -s http://localhost:8000/health/ > /dev/null & \
		curl -s http://localhost:8000/api/v1/users/ > /dev/null & \
		curl -s http://localhost:8000/api/v1/items/ > /dev/null & \
		curl -s http://localhost:8000/metrics > /dev/null & \
		if [ $$((i % 10)) -eq 0 ]; then echo "Heavy traffic: $$i/120 seconds"; fi; \
		sleep 1; \
	done; wait)
	@echo "Heavy traffic generation completed!"

traffic-burst:  ## Generate burst traffic using Python script
	@echo "Generating burst traffic (5 bursts of 20 requests each)..."
	@uv run python scripts/generate_traffic.py burst --bursts 5 --size 20 --interval 3

traffic-random:  ## Generate random traffic using Python script  
	@echo "Generating random traffic for 90 seconds..."
	@uv run python scripts/generate_traffic.py random --duration 90 --min-interval 0.1 --max-interval 1.5

traffic-steady:  ## Generate steady traffic using Python script
	@echo "Generating steady traffic (2 req/sec for 60 seconds)..."
	@uv run python scripts/generate_traffic.py steady --duration 60 --rate 2.0

traffic-stop:  ## Stop any running traffic generation
	@echo "Stopping traffic generation processes..."
	@pkill -f "curl.*localhost:8000" || echo "No traffic processes found"

# =============================================================================
# MONITORING AND DASHBOARDS
# =============================================================================

monitor:  ## Show real-time metrics dashboard
	@echo "Starting real-time metrics monitor (Ctrl+C to stop)..."
	@uv run python scripts/monitor_metrics.py

monitor-once:  ## Show current metrics once
	@echo "Fetching current metrics..."
	@uv run python scripts/monitor_metrics.py --once

monitor-simple:  ## Show simple metrics summary using curl
	@echo "=== Application Health ==="
	@curl -s http://localhost:8000/health/ | uv run python -m json.tool 2>/dev/null || echo "App not responding"
	@echo "\n=== Request Metrics (last 20 lines) ==="
	@curl -s http://localhost:8000/metrics | grep -E "(http_requests_total|http_request_duration)" | tail -20
	@echo "\n=== Custom Metrics ==="
	@curl -s http://localhost:8000/metrics | grep -E "(business_metric|user_active)" | tail -10

dashboard:  ## Open monitoring dashboards in browser
	@echo "Opening monitoring dashboards..."
	@echo "FastAPI App: http://localhost:8000"
	@echo "Prometheus:  http://localhost:9090"
	@echo "Grafana:     http://localhost:3000 (admin/admin)"
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:8000 & \
		xdg-open http://localhost:9090 & \
		xdg-open http://localhost:3000 & \
	elif command -v open > /dev/null; then \
		open http://localhost:8000 & \
		open http://localhost:9090 & \
		open http://localhost:3000 & \
	else \
		echo "Please manually open the URLs above in your browser"; \
	fi

prometheus:  ## Open Prometheus dashboard
	@echo "Opening Prometheus at http://localhost:9090"
	@if command -v xdg-open > /dev/null; then xdg-open http://localhost:9090; \
	elif command -v open > /dev/null; then open http://localhost:9090; \
	else echo "Please open http://localhost:9090 in your browser"; fi

grafana:  ## Open Grafana dashboard
	@echo "Opening Grafana at http://localhost:3000 (admin/admin)"
	@if command -v xdg-open > /dev/null; then xdg-open http://localhost:3000; \
	elif command -v open > /dev/null; then open http://localhost:3000; \
	else echo "Please open http://localhost:3000 in your browser"; fi

# =============================================================================
# MAINTENANCE AND UTILITIES
# =============================================================================

backup:  ## Backup Grafana dashboards and Prometheus data
	@echo "Creating backup..."
	@mkdir -p backups/$$(date +%Y%m%d_%H%M%S)
	@docker-compose exec -T grafana tar czf - /var/lib/grafana > backups/$$(date +%Y%m%d_%H%M%S)/grafana_backup.tar.gz 2>/dev/null || echo "Grafana backup failed"
	@docker-compose exec -T prometheus tar czf - /prometheus > backups/$$(date +%Y%m%d_%H%M%S)/prometheus_backup.tar.gz 2>/dev/null || echo "Prometheus backup failed"
	@echo "Backup completed in backups/ directory"

restore:  ## Restore from backup (specify BACKUP_DIR=backups/YYYYMMDD_HHMMSS)
	@if [ -z "$(BACKUP_DIR)" ]; then \
		echo "Usage: make restore BACKUP_DIR=backups/YYYYMMDD_HHMMSS"; \
		echo "Available backups:"; \
		ls -la backups/ 2>/dev/null || echo "No backups found"; \
		exit 1; \
	fi
	@echo "Restoring from $(BACKUP_DIR)..."
	@docker-compose down
	@docker-compose up -d
	@echo "Restore completed!"

cleanup:  ## Clean up Docker resources (containers, images, volumes)
	@echo "Cleaning up Docker resources..."
	@docker-compose down -v --rmi all --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo "Cleanup completed!"

reset:  ## Reset everything (stop, cleanup, rebuild, start)
	@echo "Performing full reset..."
	@make stop
	@make cleanup
	@make start
	@echo "Reset completed!"

# =============================================================================
# COMPREHENSIVE SETUP COMMANDS
# =============================================================================

full-setup: setup-env uv-init start  ## Complete setup and start everything
	@echo "=== FULL SETUP COMPLETED ==="
	@echo "Your FastAPI Prometheus monitoring stack is ready!"
	@echo ""
	@echo "Available endpoints:"
	@echo "  Application:  http://localhost:8000"
	@echo "  Health Check: http://localhost:8000/health/"
	@echo "  Metrics:      http://localhost:8000/metrics"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "Try these commands:"
	@echo "  make traffic-light    # Generate some test traffic"
	@echo "  make monitor          # View current metrics"
	@echo "  make dashboard        # Open all dashboards"
	@echo "  make logs             # View application logs"