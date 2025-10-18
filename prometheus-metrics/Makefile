# Makefile for FastAPI Prometheus Metrics Application

.PHONY: help
help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: start
start:  ## Start all microservices with Docker
	./start-microservices.sh

.PHONY: init-data
init-data:  ## Initialize sample data for microservices
	python scripts/init_microservices_data.py

.PHONY: restart
restart:  ## Restart all microservices
	@echo "Restarting all microservices..."
	docker-compose -f docker-compose.microservices.yml down
	docker-compose -f docker-compose.microservices.yml up -d
	@echo "Microservices restarted!"

.PHONY: status
status:  ## Show status of all containers
	@echo "Container status:"
	@docker-compose -f docker-compose.microservices.yml ps

.PHONY: stop
stop:  ## Stop all microservices
	@echo "Stopping all microservices..."
	docker-compose -f docker-compose.microservices.yml down

.PHONY: clean
clean:  ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

.PHONY: logs
logs:  ## View logs from all microservices
	docker-compose -f docker-compose.microservices.yml logs -f

.PHONY: services-health
services-health:  ## Check health of all microservices
	curl -s http://localhost:8000/health/services | python -m json.tool

# =============================================================================
# TESTING AND QUALITY ASSURANCE
# =============================================================================
.PHONY: test
test:  ## Run all quality checks
	@echo "Running format check..."
	uv run black --verbose  microservices/
	@echo "Running import sort check..."
	uv run isort --verbose  microservices/
	@echo "Running linting..."
	uv run flake8  microservices/
	@echo "Running tests..."
	uv run pytest tests/ -vvv --tb=long


duration ?= 1800
ccr ?= 25

.PHONY: load_test
load_test:  ## Run load test script
	@echo "Running load test for $(duration) minutes with $(ccr) concurrent requests..."
	uv run python scripts/load_test.py --duration $(duration) --concurrent-requests $(ccr)

# =============================================================================
# MONITORING IN COMMAND LINE
# =============================================================================
.PHONY: monitor
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

.PHONY: monitor-once
monitor-once:  ## Show current metrics once
	@echo "Fetching current metrics..."
	@if [ -f scripts/monitor_metrics.py ]; then \
		uv run python scripts/monitor_metrics.py --once; \
	else \
		$(MAKE) monitor-simple; \
	fi

.PHONY: monitor-simple
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
