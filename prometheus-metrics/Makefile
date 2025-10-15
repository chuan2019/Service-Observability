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

clean:  ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

test:  ## Run all quality checks
	@echo "Running format check..."
	uv run black --verbose  microservices/
	@echo "Running import sort check..."
	uv run isort --verbose  microservices/
	@echo "Running linting..."
	uv run flake8  microservices/
	@echo "Running tests..."
	uv run pytest tests/ -vvv --tb=long

run:  ## Start all microservices with Docker
	./start-microservices.sh

run-demo:  ## Start core microservices for demo
	./demo-microservices.sh

docker-compose-up:  ## Start all microservices with docker-compose
	docker-compose -f docker-compose.microservices.yml up --build -d

docker-compose-down:  ## Stop all microservices
	docker-compose -f docker-compose.microservices.yml down

docker-compose-logs:  ## View logs from all microservices
	docker-compose -f docker-compose.microservices.yml logs -f

services-health:  ## Check health of all microservices
	curl -s http://localhost:8000/health/services | python -m json.tool

init-data:  ## Initialize sample data for microservices
	python scripts/init_microservices_data.py

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

start:  ## Start all microservices
	@echo "Starting all microservices..."
	docker-compose -f docker-compose.microservices.yml up -d
	@echo "Microservices started! Waiting for initialization..."
	@sleep 15
	@echo "Services should be available at:"
	@echo "  API Gateway: http://localhost:8000"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3000 (admin/admin123)"

stop:  ## Stop all microservices
	@echo "Stopping all microservices..."
	docker-compose -f docker-compose.microservices.yml down

restart:  ## Restart all microservices
	@echo "Restarting all microservices..."
	docker-compose -f docker-compose.microservices.yml down
	docker-compose -f docker-compose.microservices.yml up -d
	@echo "Microservices restarted!"

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
		curl -s http://localhost:8000/api/v1/users > /dev/null && echo -n "." || echo -n "x"; \
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
		curl -s http://localhost:8000/api/v1/orders/ > /dev/null & \
		curl -s http://localhost:8000/metrics > /dev/null & \
		if [ $$((i % 10)) -eq 0 ]; then echo "Heavy traffic: $$i/120 seconds"; fi; \
		sleep 1; \
	done; wait)
	@echo "Heavy traffic generation completed!"

traffic-realistic:  ## Generate realistic microservices traffic using Python script
	@echo "Generating realistic microservices traffic (users, orders, payments)..."
	@uv run python scripts/generate_traffic.py --duration 5

traffic-extended:  ## Generate extended realistic traffic for 15 minutes
	@echo "Generating extended realistic traffic for 15 minutes..."
	@uv run python scripts/generate_traffic.py --duration 15

# Manual endpoint testing with curl (these are for manual testing when server is running)

test-all-endpoints:  ## Test all service endpoints
	@echo "Testing all service endpoints..."
	@make test-users
	@make test-orders  
	@make test-payments
	@make test-demo

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