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

start:  ## Start all microservices with Docker
	./start-microservices.sh

init-data:  ## Initialize sample data for microservices
	python scripts/init_microservices_data.py

restart:  ## Restart all microservices
	@echo "Restarting all microservices..."
	docker-compose -f docker-compose.microservices.yml down
	docker-compose -f docker-compose.microservices.yml up -d
	@echo "Microservices restarted!"

status:  ## Show status of all containers
	@echo "Container status:"
	@docker-compose -f docker-compose.microservices.yml ps

stop:  ## Stop all microservices
	@echo "Stopping all microservices..."
	docker-compose -f docker-compose.microservices.yml down

clean:  ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

logs:  ## View logs from all microservices
	docker-compose -f docker-compose.microservices.yml logs -f

services-health:  ## Check health of all microservices
	curl -s http://localhost:8000/health/services | python -m json.tool



# =============================================================================
# TESTING AND QUALITY ASSURANCE
# =============================================================================

test:  ## Run all quality checks
	@echo "Running format check..."
	uv run black --verbose  microservices/
	@echo "Running import sort check..."
	uv run isort --verbose  microservices/
	@echo "Running linting..."
	uv run flake8  microservices/
	@echo "Running tests..."
	uv run pytest tests/ -vvv --tb=long

load_test:  ## Run load test script
	@echo "Running load test for 5 minutes..."
	uv run python scripts/load_test.py --duration 300 --concurrency 20

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

traffic-stop:  ## Stop any running traffic generation
	@echo "Stopping traffic generation processes..."
	@pkill -f "curl.*localhost:8000" || echo "No traffic processes found"

# =============================================================================
# MONITORING AND DASHBOARDS
# =============================================================================

monitor:  ## Show real-time metrics dashboard
	@echo "Starting real-time metrics monitor (Ctrl+C to stop)..."
	@echo "Note: This requires the monitor_metrics.py script"
	@if [ -f scripts/monitor_metrics.py ]; then \
		uv run python scripts/monitor_metrics.py; \
	else \
		echo "Error: scripts/monitor_metrics.py not found"; \
		echo "Using simple monitoring instead..."; \
		$(MAKE) monitor-simple; \
	fi

monitor-once:  ## Show current metrics once
	@echo "Fetching current metrics..."
	@if [ -f scripts/monitor_metrics.py ]; then \
		uv run python scripts/monitor_metrics.py --once; \
	else \
		$(MAKE) monitor-simple; \
	fi

monitor-simple:  ## Show simple metrics summary using curl
	@echo "=== Microservices Health ==="
	@curl -s http://localhost:8000/health/services 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Services health check not available"
	@echo ""
	@echo "=== API Gateway Health ==="
	@curl -s http://localhost:8000/health 2>/dev/null || echo "API Gateway not responding"
	@echo ""
	@echo "=== User Service Metrics Sample ==="
	@curl -s http://localhost:8001/metrics 2>/dev/null | grep -E "^(http_requests_total|http_request_duration|user_service)" | head -10 || echo "User service metrics not available"
	@echo ""
	@echo "=== Product Service Metrics Sample ==="
	@curl -s http://localhost:8002/metrics 2>/dev/null | grep -E "^(http_requests_total|http_request_duration|product_service)" | head -10 || echo "Product service metrics not available"
	@echo ""
	@echo "=== Prometheus Status ==="
	@curl -s http://localhost:9090/-/healthy 2>/dev/null && echo "Prometheus: healthy" || echo "Prometheus: not available"
	@echo ""
	@echo "=== Grafana Status ==="
	@curl -s http://localhost:3000/api/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Grafana: not available"

dashboard:  ## Open monitoring dashboards in browser
	@echo "Opening monitoring dashboards..."
	@echo ""
	@echo "Available URLs:"
	@echo "  API Gateway:  http://localhost:8000"
	@echo "  User Service: http://localhost:8001"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3000 (admin/admin123)"
	@echo ""
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open http://localhost:8000 2>/dev/null & \
		xdg-open http://localhost:9090 2>/dev/null & \
		xdg-open http://localhost:3000 2>/dev/null & \
		echo "Dashboards opened in browser"; \
	elif command -v open > /dev/null 2>&1; then \
		open http://localhost:8000 2>/dev/null & \
		open http://localhost:9090 2>/dev/null & \
		open http://localhost:3000 2>/dev/null & \
		echo "Dashboards opened in browser"; \
	else \
		echo "Could not auto-open browser. Please manually open the URLs above."; \
	fi

prometheus:  ## Open Prometheus dashboard
	@echo "Opening Prometheus at http://localhost:9090"
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open http://localhost:9090 2>/dev/null; \
	elif command -v open > /dev/null 2>&1; then \
		open http://localhost:9090 2>/dev/null; \
	else \
		echo "Please open http://localhost:9090 in your browser"; \
	fi

grafana:  ## Open Grafana dashboard
	@echo "Opening Grafana at http://localhost:3000 (admin/admin123)"
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open http://localhost:3000 2>/dev/null; \
	elif command -v open > /dev/null 2>&1; then \
		open http://localhost:3000 2>/dev/null; \
	else \
		echo "Please open http://localhost:3000 in your browser"; \
	fi
