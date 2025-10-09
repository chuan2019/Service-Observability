# FastAPI Prometheus Metrics Integration

A comprehensive FastAPI application demonstrating Prometheus metrics integration for monitoring and observability.

## Quick Start

```bash
# Complete setup and start everything
make full-setup

# Generate test traffic
make traffic-light

# Monitor metrics in real-time
make monitor

# Open all dashboards
make dashboard
```

## Features

- **FastAPI Application** with multiple endpoints
- **Prometheus Metrics** integration with custom middleware
- **Health Checks** for Kubernetes readiness/liveness probes
- **Custom Business Metrics** for application-specific monitoring
- **Docker Support** with docker-compose for easy deployment
- **Grafana Integration** for metrics visualization
- **Advanced Traffic Generation** with Python scripts
- **Real-time Monitoring Dashboard** 
- **Comprehensive Make Commands** for operations
- **Unit Tests** with pytest
- **Comprehensive Documentation**

## Project Structure

```
metrics_01/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Application configuration
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── metrics.py             # Prometheus metrics middleware
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py              # Health check endpoints
│   │   ├── api.py                 # Main API endpoints
│   │   └── tasks.py               # Background task endpoints
│   └── services/
│       ├── __init__.py
│       └── metrics_service.py     # Custom metrics service
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── test_health.py            # Health endpoint tests
│   └── test_metrics.py           # Metrics tests
├── config/
│   ├── prometheus.yml            # Prometheus configuration
│   └── grafana/
│       ├── datasources/
│       │   └── prometheus.yml
│       └── dashboards/
│           └── dashboard.yml
├── docker/
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Metrics Overview

### HTTP Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, and status code
- `http_request_duration_seconds` - HTTP request duration histogram
- `http_request_size_bytes` - HTTP request size histogram
- `http_response_size_bytes` - HTTP response size histogram
- `http_requests_active` - Number of active HTTP requests

### Business Metrics
- `user_operations_total` - User-related operations (get, create, etc.)
- `task_operations_total` - Task-related operations (created, completed, failed)
- `api_errors_total` - API errors by endpoint and error type
- `business_processing_seconds` - Business operation processing time
- `active_sessions` - Number of active user sessions
- `memory_usage_bytes` - Memory usage by component

## Quick Start

### Local Development

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/metrics_01
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env file as needed
   ```

4. **Run the application:**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health/
   - Metrics: http://localhost:8000/metrics

## Make Commands

This project includes comprehensive Make commands for easy operations. See [MAKEFILE_COMMANDS.md](docs/MAKEFILE_COMMANDS.md) for detailed documentation.

### Essential Commands

```bash
# Complete setup and start everything
make full-setup

# Docker operations
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make status         # Show container status
make logs           # View all logs

# Traffic generation
make traffic-light  # Light traffic (1 req/sec)
make traffic-medium # Medium traffic (5 req/sec)
make traffic-heavy  # Heavy concurrent traffic
make traffic-burst  # Burst traffic patterns

# Monitoring
make monitor        # Real-time metrics dashboard
make monitor-once   # One-time metrics check
make dashboard      # Open all dashboards

# Development
make test           # Run tests
make format         # Format code
make lint           # Run linting
make check          # All quality checks

# Maintenance
make backup         # Backup data
make cleanup        # Clean Docker resources
make reset          # Full reset
```

Use `make help` to see all available commands.

### Docker Deployment

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access services:**
   - FastAPI App: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin123)

## API Endpoints

### Health Endpoints
- `GET /health/` - Basic health check
- `GET /health/ready` - Readiness probe for Kubernetes
- `GET /health/live` - Liveness probe for Kubernetes

### API Endpoints
- `GET /api/v1/users` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/users` - Create new user
- `GET /api/v1/slow-endpoint` - Slow endpoint for testing
- `GET /api/v1/memory-intensive` - Memory-intensive endpoint

### Task Endpoints
- `POST /tasks/` - Create background task
- `GET /tasks/` - List all tasks
- `GET /tasks/{task_id}` - Get task status

### Metrics Endpoint
- `GET /metrics` - Prometheus metrics in text format

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

## Monitoring Setup

### Prometheus Queries

Some useful Prometheus queries for monitoring:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"4..|5.."}[5m])

# Response time percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active requests
http_requests_active

# Business metrics
rate(user_operations_total[5m])
```

### Grafana Dashboard

The included Grafana configuration provides:
- HTTP request metrics visualization
- Error rate monitoring
- Response time percentiles
- Custom business metrics
- System resource usage

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `PROJECT_NAME` - Application name
- `ENVIRONMENT` - Environment (development/production)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)
- `METRICS_ENABLED` - Enable/disable metrics collection

### Prometheus Configuration

The `config/prometheus.yml` file defines:
- Scrape intervals
- Target endpoints
- Metric collection rules

## Development

### Code Quality

The project includes configuration for:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **pytest** for testing

Run quality checks:
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Run tests
pytest
```

### Adding Custom Metrics

To add custom metrics:

1. Define metrics in `app/services/metrics_service.py`
2. Use the metrics service in your endpoints
3. Update tests to verify metrics collection

Example:
```python
from app.services.metrics_service import MetricsService

metrics_service = MetricsService()

# In your endpoint
@router.get("/my-endpoint")
async def my_endpoint():
    metrics_service.increment_counter("my_custom_metric")
    return {"message": "Hello"}
```

## Production Considerations

### Security
- Remove debug endpoints in production
- Use proper authentication/authorization
- Secure metrics endpoint access
- Use HTTPS

### Performance
- Configure appropriate scrape intervals
- Monitor metrics cardinality
- Use metric aggregation for high-volume metrics
- Configure proper retention policies

### Scaling
- Use external metrics storage (e.g., Prometheus with external storage)
- Consider metrics federation for multi-instance deployments
- Implement proper service discovery

## Troubleshooting

### Common Issues

1. **Metrics not appearing:**
   - Check if middleware is properly installed
   - Verify Prometheus scrape configuration
   - Check application logs

2. **High memory usage:**
   - Monitor metrics cardinality
   - Implement metric cleanup
   - Configure proper retention

3. **Performance impact:**
   - Adjust scrape intervals
   - Use sampling for high-volume metrics
   - Monitor middleware overhead

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m app.main
```

Check metrics format:
```bash
curl http://localhost:8000/metrics
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)