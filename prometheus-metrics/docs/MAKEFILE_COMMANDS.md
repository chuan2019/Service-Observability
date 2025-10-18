# Makefile Commands Reference

This document provides a comprehensive guide to all available Make commands for the FastAPI Microservices Prometheus Metrics project.

## Quick Start

```bash
# Start all microservices
make start

# Initialize sample data
make init-data

# Monitor metrics in real-time
make monitor

# Check service health
make services-health
```

## Command Categories

### Core Operations

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands with descriptions |
| `make start` | Start all microservices with Docker Compose |
| `make stop` | Stop all microservices and clean up |
| `make restart` | Restart all microservices (down + up) |
| `make status` | Show status of all running containers |
| `make logs` | View logs from all microservices (follow mode) |

### Data Management

| Command | Description |
|---------|-------------|
| `make init-data` | Initialize sample data for microservices (products, users, inventory, etc.) |

### Health Checks

| Command | Description |
|---------|-------------|
| `make services-health` | Check health status of all microservices via API Gateway |

### Code Quality and Testing

| Command | Description |
|---------|-------------|
| `make clean` | Clean up Python cache files, __pycache__, .pyc files, and test artifacts |
| `make test` | Run all quality checks: format (black), import sort (isort), lint (flake8), and tests (pytest) |

### Load Testing

| Command | Parameters | Description |
|---------|------------|-------------|
| `make load_test` | `duration=1800` (minutes)<br>`ccr=25` (concurrent requests) | Run load test script with configurable duration and concurrency |

**Examples:**
```bash
# Run load test for 30 minutes with 50 concurrent requests
make load_test duration=1800 ccr=50

# Run load test with default values (30 minutes, 25 concurrent requests)
make load_test
```

### Monitoring

| Command | Description |
|---------|-------------|
| `make monitor` | Show real-time metrics dashboard (requires monitor_metrics.py script) |
| `make monitor-once` | Show current metrics snapshot once |
| `make monitor-simple` | Show simple metrics summary using curl (fallback if no script) |

## Detailed Usage Examples

### Complete Workflow

```bash
# 1. Start all microservices
make start

# 2. Initialize sample data (products, users, inventory)
make init-data

# 3. Check all services are healthy
make services-health

# 4. Monitor in real-time
make monitor

# 5. Run a load test (30 minutes, 25 concurrent requests)
make load_test

# 6. Check logs if needed
make logs
```

### Development Workflow

```bash
# Start services
make start

# Make code changes in microservices/

# Run quality checks (format, lint, test)
make test

# Restart to apply changes
make restart

# Clean up cache files
make clean
```

### Load Testing Scenarios

```bash
# Light load test (5 minutes, 10 concurrent requests)
make load_test duration=300 ccr=10

# Medium load test (15 minutes, 25 concurrent requests)
make load_test duration=900 ccr=25

# Heavy load test (30 minutes, 50 concurrent requests)
make load_test duration=1800 ccr=50

# Stress test (1 hour, 100 concurrent requests)
make load_test duration=3600 ccr=100
```

### Monitoring and Troubleshooting

```bash
# Quick metrics check
make monitor-once

# Continuous monitoring dashboard
make monitor

# Check all services health
make services-health

# View all logs (follow mode)
make logs

# Check container status
make status

# Restart if services are having issues
make restart
```

### Python Scripts

The project includes Python scripts for various operations:

#### Load Testing Script
```bash
# Run load test with custom parameters
uv run python scripts/load_test.py --duration 1800 --concurrent-requests 25

# Run with custom options
uv run python scripts/load_test.py \
  --duration 3600 \
  --concurrent-requests 50 \
  --base-url http://localhost:8000
```

#### Data Initialization Script
```bash
# Initialize sample data
python scripts/init_microservices_data.py

# This creates:
# - Sample products (electronics, furniture, kitchen items)
# - Sample users
# - Inventory stock
# - Sample orders
```

#### Traffic Generation Script
```bash
# Generate various traffic patterns
uv run python scripts/generate_traffic.py
```

#### Monitoring Script (if available)
```bash
# Real-time dashboard
uv run python scripts/monitor_metrics.py

# One-time metrics check
uv run python scripts/monitor_metrics.py --once
```

## Service URLs

When services are running, they are available at:

### Microservices (Direct Access)
- **User Service**: http://localhost:8001
  - Health: http://localhost:8001/health
  - Metrics: http://localhost:8001/metrics
- **Product Service**: http://localhost:8002
  - Health: http://localhost:8002/health
  - Metrics: http://localhost:8002/metrics
- **Inventory Service**: http://localhost:8003
  - Health: http://localhost:8003/health
  - Metrics: http://localhost:8003/metrics
- **Order Service**: http://localhost:8004
  - Health: http://localhost:8004/health
  - Metrics: http://localhost:8004/metrics
- **Payment Service**: http://localhost:8005
  - Health: http://localhost:8005/health
  - Metrics: http://localhost:8005/metrics
- **Notification Service**: http://localhost:8006
  - Health: http://localhost:8006/health
  - Metrics: http://localhost:8006/metrics

### API Gateway (Nginx)
- **API Gateway**: http://localhost:8000
  - Gateway Health: http://localhost:8000/health
  - All Services Health: http://localhost:8000/health/services
  - Users API: http://localhost:8000/api/users
  - Products API: http://localhost:8000/api/products
  - Inventory API: http://localhost:8000/api/inventory
  - Orders API: http://localhost:8000/api/orders
  - Payments API: http://localhost:8000/api/payments
  - Notifications API: http://localhost:8000/api/notifications

### Metrics Collection via Gateway
- **User Service Metrics**: http://localhost:8000/metrics/users
- **Product Service Metrics**: http://localhost:8000/metrics/products
- **Inventory Service Metrics**: http://localhost:8000/metrics/inventory
- **Order Service Metrics**: http://localhost:8000/metrics/orders
- **Payment Service Metrics**: http://localhost:8000/metrics/payments
- **Notification Service Metrics**: http://localhost:8000/metrics/notifications

### Monitoring Stack
- **Prometheus**: http://localhost:9090
  - Targets: http://localhost:9090/targets
  - Alerts: http://localhost:9090/alerts
  - Rules: http://localhost:9090/rules
  - Graph: http://localhost:9090/graph
- **Grafana**: http://localhost:3000
  - Default credentials: admin / admin
- **PostgreSQL Exporter**: http://localhost:9187/metrics

### Database
- **PostgreSQL**: localhost:5432
  - Database: ecommerce
  - User: postgres
  - Password: password

## Architecture

```
microservices/
├── shared/                    # Shared components
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   ├── middleware.py         # PrometheusMiddleware
│   └── database.py           # Database configuration
├── user-service/             # User management (port 8001)
├── product-service/          # Product catalog (port 8002)
├── inventory-service/        # Inventory & stock (port 8003)
├── order-service/            # Order processing (port 8004)
├── payment-service/          # Payment handling (port 8005)
├── notification-service/     # Notifications (port 8006)
└── api-gateway/             # Nginx API Gateway (port 8000)

scripts/
├── init_microservices_data.py  # Initialize sample data
├── generate_traffic.py         # Traffic generation
├── load_test.py               # Load testing
└── monitor_metrics.py         # Metrics monitoring

config/
├── prometheus-microservices.yml  # Prometheus configuration
├── alert_rules.yml              # Alert rules
├── grafana-dashboard.json       # Grafana dashboard
├── ALERTING.md                  # Alerting documentation
└── POSTGRES_MONITORING.md       # PostgreSQL monitoring guide

tests/
└── test_microservices.py       # Integration tests

docker-compose.microservices.yml  # Docker Compose configuration
```

## Tips and Best Practices

1. **Always start with `make start`** to bring up all services
2. **Run `make init-data`** after first start to populate sample data
3. **Use `make status`** to check if all services are running
4. **Use `make services-health`** to verify all microservices are healthy
5. **Check logs with `make logs`** if something isn't working
6. **Use `make monitor`** for real-time feedback during load testing
7. **Run `make test`** to ensure code quality before committing
8. **The `make restart`** command is useful when services need a fresh start

## Monitoring Workflow

```bash
# 1. Start services
make start

# 2. Wait for services to be healthy (check status)
make status

# 3. Initialize data
make init-data

# 4. Check all services are responding
make services-health

# 5. Start monitoring dashboard
make monitor

# 6. In another terminal, run load test
make load_test duration=600 ccr=20

# 7. Watch metrics in Prometheus
open http://localhost:9090

# 8. View dashboards in Grafana
open http://localhost:3000
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Services won't start | Check `make status` and `make logs` for errors |
| No metrics visible | Run `make init-data` and generate some traffic with `make load_test` |
| Service unhealthy | Check logs: `make logs` and look for specific service errors |
| Database connection issues | Verify postgres container is healthy with `make status` |
| Prometheus targets down | Check `make status`, verify all services are running |
| API Gateway 502 errors | Services may not be ready yet, check `make services-health` |
| Port conflicts | Stop services with `make stop` and check for processes using ports 8000-8006, 9090, 3000 |

## Environment Variables

Each microservice uses these environment variables:

- `ENVIRONMENT`: production/development
- `DATABASE_URL`: PostgreSQL connection string (postgresql+asyncpg://...)
- `PORT`: Service-specific port (automatically set per service)

Database configuration:
- `POSTGRES_DB`: ecommerce
- `POSTGRES_USER`: postgres
- `POSTGRES_PASSWORD`: password

## Testing

```bash
# Run all tests with quality checks
make test

# This includes:
# 1. Code formatting (black)
# 2. Import sorting (isort)
# 3. Linting (flake8)
# 4. Integration tests (pytest)

# Run tests manually
uv run pytest tests/ -vvv --tb=long
```

## Performance Monitoring

### Key Metrics to Monitor

1. **HTTP Request Metrics**
   - `http_requests_total` - Total requests by service, endpoint, method, status
   - `http_request_duration_seconds` - Request latency histogram
   - `http_requests_in_progress` - Current concurrent requests

2. **Service-Specific Metrics**
   - `inventory_service_operations_total` - Inventory operations (create, reserve, release)
   - `inventory_service_stock_level` - Current stock levels per product
   - `order_service_operations_total` - Order operations
   - `payment_service_operations_total` - Payment operations

3. **Database Metrics (postgres_exporter)**
   - `pg_up` - PostgreSQL availability
   - `pg_stat_database_numbackends` - Active connections
   - `pg_database_size_bytes` - Database size
   - `pg_stat_database_n_dead_tup` - Dead tuples (needs VACUUM)

4. **Alert Status**
   - Check http://localhost:9090/alerts for active alerts
   - Database, performance, and availability alerts configured

## Load Testing Best Practices

1. **Start with low concurrency** and gradually increase:
   ```bash
   make load_test duration=300 ccr=10    # Warm-up
   make load_test duration=600 ccr=25    # Normal load
   make load_test duration=900 ccr=50    # High load
   ```

2. **Monitor during load tests**:
   - Keep `make monitor` running in one terminal
   - Watch Prometheus graphs in browser
   - Check Grafana dashboards for visualizations

3. **Check for errors**:
   ```bash
   # Monitor logs during test
   make logs
   
   # Check for error rates in Prometheus
   rate(http_requests_total{status_code=~"5.."}[5m])
   ```

4. **System resource monitoring**:
   - Watch `http_requests_in_progress` gauge
   - Monitor database connections
   - Check response time percentiles
