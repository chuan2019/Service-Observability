# FastAPI Jaeger Tracing Demo

A comprehensive demonstration of distributed tracing with FastAPI and Jaeger using OpenTelemetry. This project shows how to implement, configure, and monitor distributed tracing in a microservices architecture.

## Features

- **FastAPI Application** with OpenTelemetry instrumentation
- **Jaeger Integration** for distributed tracing visualization
- **Multiple Service Simulation** (User, Order, Payment services)
- **Custom Spans** with detailed attributes and events
- **Docker Deployment** with Docker Compose
- **Traffic Generation** scripts for testing and demos
- **Load Testing** tools for performance analysis
- **Development Environment** with `uv` for dependency management

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Jaeger Agent   │    │   Jaeger UI     │
│                 │───▶│                 │───▶│                 │
│ OpenTelemetry   │    │ Trace Collector │    │ Query & Display │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Service   │    │ Order Service   │    │Payment Service  │
│                 │    │                 │    │                 │
│ Custom Spans    │    │ Custom Spans    │    │ Custom Spans    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- [UV](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose (optional, for containerized deployment)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd fastapi-jaeger-tracing

# Run the setup script
./scripts/setup.sh
```

### 2. Start Development Environment

```bash
# Start Jaeger
make run-jaeger

# Start FastAPI application (in another terminal)
make run-dev
```

### 3. Generate Traffic and View Traces

```bash
# Generate sample traffic
make traffic

# View traces in Jaeger UI
open http://localhost:16686
```

## Documentation

### Project Structure

```
fastapi-jaeger-tracing/
├── app/                          # FastAPI application
│   ├── main.py                  # Main application with endpoints
│   └── services/                # Service modules
│       ├── user_service.py      # User management with tracing
│       ├── order_service.py     # Order processing with tracing
│       └── payment_service.py   # Payment processing with tracing
├── config/                      # Configuration modules
│   └── tracing.py              # OpenTelemetry configuration
├── docker/                     # Docker configurations
│   └── Dockerfile              # Application container
├── scripts/                    # Utility scripts
│   ├── setup.sh               # Project setup script
│   ├── generate_traffic.py    # Traffic generation tool
│   └── load_test.py           # Load testing tool
├── tests/                      # Test files
├── docker-compose.yml          # Production deployment
├── docker-compose.dev.yml      # Development services
├── Makefile                    # Development commands
└── pyproject.toml             # Project dependencies
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with basic info |
| `/health` | GET | Health check endpoint |
| `/users/{user_id}` | GET | Get user by ID |
| `/users` | POST | Create new user |
| `/orders/{order_id}` | GET | Get order by ID |
| `/orders` | POST | Create new order |
| `/payments` | POST | Process payment |
| `/demo/full-flow/{user_id}` | GET | Demonstrate full service flow |

### Tracing Features

#### Automatic Instrumentation
- HTTP requests and responses
- Database queries (if configured)
- External service calls

#### Custom Spans
- Service-level operations
- Business logic tracing
- Error tracking and attributes
- Performance metrics

#### Trace Attributes
- Service names and versions
- HTTP methods and status codes
- User IDs and business entities
- Processing times and outcomes
- Error details and stack traces

## Development

### Environment Setup

```bash
# Install dependencies
make install-dev

# Setup development environment
make dev-setup
```

### Running the Application

```bash
# Development mode with hot reload
make run-dev

# Production mode
make run
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Type checking
make type-check

# Run tests
make test

# Test with coverage
make test-coverage
```

### Docker Development

```bash
# Start all services
make docker-up

# Start development services only
make docker-up-dev

# View logs
make docker-logs

# Stop services
make docker-down
```

## Traffic Generation

### Basic Traffic Generation

```bash
# Generate realistic user activity for 60 seconds
make traffic

# Run demo scenarios
make traffic-demo

# Stress test
make traffic-stress
```

### Load Testing

```bash
# Basic load test
make load-test

# Heavy load test
make load-test-heavy

# Custom load test
uv run python scripts/load_test.py --users 20 --requests 100 --ramp-up 30
```

### Traffic Generation Options

```bash
# Activity mode (realistic user behavior)
python scripts/generate_traffic.py --mode activity --duration 120

# Demo mode (specific scenarios)
python scripts/generate_traffic.py --mode demo

# Stress mode (high load)
python scripts/generate_traffic.py --mode stress --rps 50 --duration 60
```

## Monitoring and Observability

### Jaeger UI

Access the Jaeger UI at `http://localhost:16686` to:

- **View Traces**: See complete request flows across services
- **Analyze Performance**: Identify bottlenecks and slow operations
- **Debug Issues**: Track errors and their root causes
- **Service Map**: Visualize service dependencies and call patterns

### Key Metrics to Monitor

1. **Request Duration**: How long requests take end-to-end
2. **Service Dependencies**: Which services call which others
3. **Error Rates**: Percentage of failed requests
4. **Throughput**: Requests per second handled
5. **Service Health**: Individual service performance

### Trace Analysis

Look for:
- **Long-running spans**: Performance bottlenecks
- **Error spans**: Failed operations and their causes
- **Service fan-out**: How requests propagate through services
- **Critical path**: The slowest part of request processing

## Docker Deployment

### Development Deployment

```bash
# Start development services
make docker-up-dev

# Services included:
# - Jaeger (tracing)
# - Redis (caching)
# - PostgreSQL (database)
```

### Production Deployment

```bash
# Build and start all services
make docker-build
make docker-up

# Services included:
# - FastAPI Main Service (port 8000)
# - User Service (port 8001)
# - Order Service (port 8002) 
# - Payment Service (port 8003)
# - Jaeger (port 16686)
```

### Service URLs

- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **User Service**: http://localhost:8001
- **Order Service**: http://localhost:8002
- **Payment Service**: http://localhost:8003
- **Jaeger UI**: http://localhost:16686

## Testing

### Unit Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Integration Tests

```bash
# Test with running services
uv run pytest tests/integration/
```

### Manual Testing

```bash
# Check service health
make health

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/users/1
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d '{"user_id": 1, "amount": 99.99}'
```

## Demo Scenarios

### Complete Demo

```bash
# Run full demo sequence
make demo

# This will:
# 1. Start all services
# 2. Generate demo traffic
# 3. Run load tests
# 4. Display results
```

### Step-by-Step Demo

1. **Start Services**
   ```bash
   make docker-up
   ```

2. **Generate Base Traffic**
   ```bash
   make traffic-demo
   ```

3. **Show Jaeger UI**
   - Open http://localhost:16686
   - Search for service: `fastapi-jaeger-demo`
   - Show trace timeline and service map

4. **Generate Load**
   ```bash
   make load-test
   ```

5. **Analyze Results**
   - Performance bottlenecks
   - Error patterns
   - Service dependencies

## Configuration

### Environment Variables

```bash
# Service configuration
SERVICE_NAME=fastapi-jaeger-demo
JAEGER_HOST=localhost
JAEGER_PORT=14268
ENVIRONMENT=development

# Application settings
DEBUG=true
LOG_LEVEL=INFO
```

### Tracing Configuration

```python
# config/tracing.py
config = TracingConfig(
    service_name="my-service",
    jaeger_host="jaeger",
    jaeger_port=14268,
    environment="production"
)
```

## Troubleshooting

### Common Issues

1. **Jaeger Not Starting**
   ```bash
   docker-compose logs jaeger
   make docker-clean
   make docker-up
   ```

2. **Application Import Errors**
   ```bash
   make clean
   make install-dev
   ```

3. **Port Conflicts**
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :16686
   ```

4. **No Traces Visible**
   - Check Jaeger connection: `curl http://localhost:16686`
   - Verify service name in Jaeger UI
   - Check application logs: `make logs-app`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
make run-dev

# View detailed logs
make logs-app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks: `make lint format test`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [OpenTelemetry Python Documentation](https://opentelemetry-python.readthedocs.io/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [UV Package Manager](https://github.com/astral-sh/uv)

## Next Steps

- Add database integration with SQLAlchemy tracing
- Implement metrics with Prometheus
- Add log correlation with trace IDs
- Integrate with service mesh (Istio)
- Add custom OpenTelemetry collectors
- Implement distributed tracing across multiple languages

---

**Happy Tracing!**