# Makefile Commands Reference

This document provides a comprehensive guide to all available Make commands for the FastAPI Prometheus metrics project.

## Quick Start

```bash
# Complete setup and get everything running
make full-setup

# Generate some test traffic
make traffic-light

# Monitor metrics in real-time
make monitor

# Open all dashboards
make dashboard
```

## Command Categories

### Development Setup

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install production dependencies |
| `make dev-install` | Install development dependencies |
| `make setup-env` | Copy example environment file |
| `make dev-setup` | Complete development setup |
| `make production-setup` | Production setup |
| `make full-setup` | Complete setup and start everything |

### Code Quality

| Command | Description |
|---------|-------------|
| `make clean` | Clean up cache and temporary files |
| `make test` | Run tests |
| `make test-coverage` | Run tests with coverage report |
| `make lint` | Run linting (flake8) |
| `make format` | Format code (black + isort) |
| `make check` | Run all quality checks |
| `make install-hooks` | Install pre-commit hooks |

### Application Management

| Command | Description |
|---------|-------------|
| `make run` | Run the application locally |
| `make run-dev` | Run in development mode with reload |
| `make health` | Check application health |
| `make metrics` | Show current metrics |

### Docker Operations

| Command | Description |
|---------|-------------|
| `make start` | Start all services (FastAPI, Prometheus, Grafana) |
| `make stop` | Stop all services |
| `make restart` | Restart all services |
| `make status` | Show container status |
| `make logs` | Show logs from all services |
| `make logs-app` | Show FastAPI application logs only |
| `make logs-prometheus` | Show Prometheus logs only |
| `make logs-grafana` | Show Grafana logs only |

### Traffic Generation

| Command | Description | Details |
|---------|-------------|---------|
| `make traffic-light` | Light traffic | 1 req/sec for 30 seconds using curl |
| `make traffic-medium` | Medium traffic | 5 req/sec for 60 seconds using curl |
| `make traffic-heavy` | Heavy concurrent traffic | Multiple concurrent requests for 2 minutes |
| `make traffic-burst` | Burst traffic | 5 bursts of 20 requests each (Python script) |
| `make traffic-random` | Random traffic | Random intervals for 90 seconds (Python script) |
| `make traffic-steady` | Steady traffic | 2 req/sec for 60 seconds (Python script) |
| `make traffic-stop` | Stop traffic generation | Kill any running traffic processes |

### Monitoring and Dashboards

| Command | Description |
|---------|-------------|
| `make monitor` | Real-time metrics dashboard (interactive) |
| `make monitor-once` | Show current metrics once |
| `make monitor-simple` | Simple metrics summary using curl |
| `make dashboard` | Open all dashboards in browser |
| `make prometheus` | Open Prometheus dashboard |
| `make grafana` | Open Grafana dashboard |

### Maintenance

| Command | Description |
|---------|-------------|
| `make backup` | Backup Grafana and Prometheus data |
| `make restore` | Restore from backup (requires BACKUP_DIR) |
| `make cleanup` | Clean up Docker resources |
| `make reset` | Full reset (stop, cleanup, rebuild, start) |

## Detailed Usage Examples

### Complete Workflow

```bash
# 1. Initial setup
make full-setup

# 2. Generate some traffic
make traffic-light

# 3. Monitor in real-time
make monitor

# 4. Open dashboards
make dashboard

# 5. Generate more complex traffic
make traffic-burst

# 6. Check logs if needed
make logs-app
```

### Development Workflow

```bash
# Setup development environment
make dev-setup

# Make code changes...

# Run quality checks
make check

# Test locally
make run-dev

# Run tests
make test-coverage
```

### Traffic Generation Patterns

```bash
# Start with light traffic to warm up
make traffic-light

# Generate steady load
make traffic-steady

# Test with burst patterns
make traffic-burst

# Random traffic patterns
make traffic-random

# Heavy concurrent load
make traffic-heavy

# Stop all traffic generation
make traffic-stop
```

### Monitoring and Troubleshooting

```bash
# Quick metrics check
make monitor-once

# Continuous monitoring
make monitor

# Check application health
make health

# View specific logs
make logs-app
make logs-prometheus
make logs-grafana

# Check container status
make status
```

### Advanced Python Scripts

The project includes advanced Python scripts for traffic generation and monitoring:

#### Traffic Generation Script
```bash
# Custom steady traffic
python scripts/generate_traffic.py steady --duration 120 --rate 3.0

# Custom burst patterns
python scripts/generate_traffic.py burst --bursts 10 --size 15 --interval 2

# Custom random traffic
python scripts/generate_traffic.py random --duration 300 --min-interval 0.05 --max-interval 3.0
```

#### Monitoring Script
```bash
# Real-time dashboard
python scripts/monitor_metrics.py

# One-time metrics check
python scripts/monitor_metrics.py --once

# Custom refresh interval
python scripts/monitor_metrics.py --refresh 2
```

## Service URLs

When services are running, they are available at:

- **FastAPI Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health/
- **Metrics Endpoint**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## File Structure

```
scripts/
├── generate_traffic.py    # Advanced traffic generation
└── monitor_metrics.py     # Real-time metrics monitoring

docker/
├── Dockerfile            # FastAPI application container
└── ...

config/
├── prometheus.yml        # Prometheus configuration
└── grafana-dashboard.json # Grafana dashboard

tests/
└── ...                   # Unit tests

app/
├── main.py              # FastAPI application
├── middleware/          # Metrics middleware
├── routers/            # API routes
└── services/           # Business logic
```

## Tips and Best Practices

1. **Always start with `make full-setup`** for initial setup
2. **Use `make status`** to check if services are running
3. **Generate traffic before checking metrics** - many metrics only appear after requests
4. **Use `make monitor`** for real-time feedback during load testing
5. **Check logs with `make logs-app`** if something isn't working
6. **Use `make cleanup`** to reset Docker environment if needed
7. **The `make reset`** command is useful when things get corrupted

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Services won't start | Try `make reset` |
| No metrics visible | Generate traffic first with `make traffic-light` |
| Grafana login issues | Use admin/admin, check `make logs-grafana` |
| Prometheus targets down | Check `make status` and `make logs-prometheus` |
| Traffic generation fails | Ensure services are running with `make status` |

## Environment Variables

The application uses these environment variables (see `.env` file):

- `ENVIRONMENT`: dev/staging/production
- `DEBUG`: true/false for debug mode
- `LOG_LEVEL`: logging level (DEBUG, INFO, WARNING, ERROR)
- `METRICS_ENABLED`: true/false to enable metrics collection

Configure these in your `.env` file after running `make setup-env`.