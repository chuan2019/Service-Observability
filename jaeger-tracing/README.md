# FastAPI + Jaeger + Kibana Observability Stack

A complete production-ready observability stack with distributed tracing, advanced analytics, and comprehensive monitoring. **Everything can be done with simple `make` commands!**

## Features

- **FastAPI Application** with OpenTelemetry instrumentation
- **Distributed Tracing** with Jaeger using OTLP protocol  
- **Advanced Analytics** with Kibana and Elasticsearch
- **Comprehensive Testing** with pytest (16 test cases, 77% coverage)
- **Traffic Generation** and load testing tools
- **Docker Compose** for easy deployment
- **Complete Makefile** for all operations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   Jaeger UI     │────│  Elasticsearch  │
│  (Port 8000)    │    │  (Port 16686)   │    │  (Port 9200)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │     Kibana      │
                                               │  (Port 5601)    │
                                               └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- UV package manager

## Quick Start (3 Commands!)

### 1. Setup Project
```bash
make setup
```

### 2. Start Everything
```bash
make full-setup
```

### 3. Run Demo
```bash
make demo
```

That's it! Your complete observability stack is running with sample data.

## All Available Commands

View all available commands:
```bash
make help
```

Output:
```
FastAPI Jaeger Tracing Demo
===========================

Available commands:
  help            Show this help message
  install         Install project dependencies using uv
  install-dev     Install development dependencies
  setup           Setup the project environment
  run             Run FastAPI application locally
  run-dev         Run FastAPI application in development mode with hot reload
  run-jaeger      Start only Jaeger using Docker Compose
  docker-build    Build Docker images
  docker-up       Start all services with Docker Compose
  docker-down     Stop all Docker services
  docker-logs     Show Docker logs
  docker-clean    Clean up Docker resources
  lint            Run linting with ruff
  format          Format code with black and ruff
  type-check      Run type checking with mypy
  test            Run tests
  test-coverage   Run tests with coverage
  traffic         Generate sample traffic (60 seconds)
  traffic-demo    Run demo traffic scenarios
  traffic-stress  Run stress test traffic
  load-test       Run comprehensive load test
  load-test-heavy Run heavy load test
  demo            Run full demo sequence
  demo-clean      Clean demo and restart
  health          Check service health
  status          Show service status
  clean           Clean up temporary files and caches
  dev-setup       Quick development setup
  full-setup      Full setup with all services
  full-stop       Stop all services and processes completely
  logs-app        Show application logs
  logs-jaeger     Show Jaeger logs
  shell-app       Open shell in main application container
  env-info        Show environment information
```

## Essential Commands

### Setup & Development
```bash
make setup          # Initial project setup
make full-setup     # Start complete observability stack
make full-stop      # Stop everything
make clean          # Clean up temporary files
```

### Running Services
```bash
make docker-up      # Start all services with Docker
make docker-down    # Stop Docker services
make run-dev        # Run FastAPI locally with hot reload
make status         # Check service status
make health         # Health check all services
```

### Testing & Quality
```bash
make test           # Run all tests (16 tests)
make test-coverage  # Run tests with coverage report (77%)
make lint           # Code linting
make format         # Format code
```

### Traffic & Load Testing
```bash
make traffic-demo   # Generate demo traffic
make load-test      # Run load test (10 users, 50 requests each)
make load-test-heavy # Heavy load test (25 users, 100 requests each)
make demo           # Complete demo sequence
```

## Service URLs

After running `make full-setup`, access:

| Service | URL | Description |
|---------|-----|-------------|
| **FastAPI** | http://localhost:8000 | Main application |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health** | http://localhost:8000/health | Health check endpoint |
| **Jaeger UI** | http://localhost:16686 | Distributed tracing visualization |
| **Kibana** | http://localhost:5601 | Advanced analytics dashboard |
| **Elasticsearch** | http://localhost:9200 | Search engine API |

## Testing

### Run Tests
```bash
make test           # All 16 tests with detailed output
make test-coverage  # Tests + coverage report (77% coverage)
```

### Generate Test Traffic
```bash
make traffic-demo   # Demo scenarios
make load-test      # Performance testing
```

## Viewing Results

### Jaeger Tracing (http://localhost:16686)
After running `make demo`:
1. Open Jaeger UI
2. Select service: `fastapi-jaeger-demo`
3. Click "Find Traces" to see all distributed traces
4. Click on individual traces to see detailed timing

### Kibana Analytics (http://localhost:5601)
Advanced trace analysis:
1. Go to **Discover**
2. Select `jaeger-span-*` index pattern
3. Explore traces with advanced queries

### Sample Kibana Queries
```kuery
# Find all traces for main service
service: "fastapi-jaeger-demo"

# Find error traces
error: true

# Find slow operations (> 1 second)
duration_ms: >1000

# Find POST requests with errors
method: "POST" AND error: true
```

## Development Workflows

### Quick Development Cycle
```bash
make setup          # One-time setup
make run-dev        # Start with hot reload
# Make code changes
make test           # Run tests
make format         # Format code
```

### Full Testing Cycle
```bash
make full-setup     # Start all services
make demo           # Generate sample data
make test-coverage  # Comprehensive testing
make full-stop      # Clean shutdown
```

### Debug Issues
```bash
make status         # Check service status
make health         # Health check endpoints
make logs-app       # View application logs
make logs-jaeger    # View Jaeger logs
```

## Project Structure

```
jaeger-tracing/
├── Makefile              # All commands in one place!
├── app/                  # FastAPI application
│   ├── main.py          # Main app with tracing
│   └── services/        # Business logic services
├── config/              # Configuration
│   └── tracing.py       # OpenTelemetry setup
├── tests/               # Test suite (16 tests, 77% coverage)
│   └── test_main.py     # Comprehensive tests
├── scripts/             # Traffic generation & utilities
├── docker/              # Docker configuration
├── kibana/              # Kibana configuration
├── docker-compose.yml   # Complete stack definition
└── pyproject.toml       # Dependencies
```

## Common Use Cases

### Demo for Presentation
```bash
make demo               # Complete automated demo
```

### Development
```bash
make dev-setup         # Quick dev environment
make run-dev           # Hot reload development
```

### Testing
```bash
make test              # Unit tests
make load-test         # Performance testing
```

### Production Simulation
```bash
make full-setup        # Complete production-like stack
make traffic-stress    # Stress testing
```

## Configuration

All services are pre-configured and work out of the box! Key configurations:

- **OpenTelemetry**: OTLP HTTP endpoint (port 4318)
- **Jaeger**: UI on port 16686, stores data in Elasticsearch
- **Kibana**: Analytics UI on port 5601
- **Elasticsearch**: Data storage on port 9200

## API Endpoints

After running `make full-setup`, test these endpoints:

| Endpoint | Method | Description | Test Command |
|----------|--------|-------------|--------------|
| `/health` | GET | Health check | `curl http://localhost:8000/health` |
| `/users` | POST | Create user | `curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name":"John","email":"john@example.com"}'` |
| `/users/{id}` | GET | Get user | `curl http://localhost:8000/users/1` |
| `/orders` | POST | Create order | `curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d '{"user_id":1,"product":"Widget","amount":99.99}'` |
| `/orders/{id}` | GET | Get order | `curl http://localhost:8000/orders/101` |
| `/payments` | POST | Process payment | `curl -X POST http://localhost:8000/payments -H "Content-Type: application/json" -d '{"amount":99.99,"method":"credit_card"}'` |
| `/demo/full-flow/{id}` | GET | Full flow demo | `curl http://localhost:8000/demo/full-flow/1` |

## Observability Features

### Automatic Tracing
Every request is automatically traced with:
- HTTP request/response details
- Database operations (simulated)
- Business logic timing
- Error tracking and exception details
- Service dependencies

### What You'll See in Jaeger
- Complete request flows across services
- Performance breakdown by operation
- Error traces with stack traces
- Service dependency maps
- Response time distributions

## Troubleshooting

### Quick Debugging
```bash
make status         # Check all services
make health         # Health check endpoints
make logs-app       # View application logs
make logs-jaeger    # View Jaeger logs
```

### Common Issues & Solutions

| Issue | Command | Solution |
|-------|---------|----------|
| Services not starting | `make status` | Check Docker is running, ports available |
| No traces in Jaeger | `make health` | Verify all services are healthy |
| Tests failing | `make test` | Check error output, run `make format` |
| Port conflicts | `make full-stop` | Stop all services, then restart |

### Manual Health Checks
```bash
curl http://localhost:8000/health    # FastAPI
curl http://localhost:16686/         # Jaeger UI
curl http://localhost:5601/api/status # Kibana
curl http://localhost:9200/_cluster/health # Elasticsearch
```

## Production Ready

### Complete Stack Deployment
```bash
make docker-build   # Build all images
make full-setup     # Deploy complete stack
make demo           # Validate with demo data
```

### Services Included
- **FastAPI Main Service** (port 8000) - Primary application
- **User Service** (port 8001) - User management microservice  
- **Order Service** (port 8002) - Order processing microservice
- **Payment Service** (port 8003) - Payment processing microservice
- **Jaeger** (port 16686) - Distributed tracing UI
- **Elasticsearch** (port 9200) - Data storage
- **Kibana** (port 5601) - Analytics dashboard

## Documentation & Resources

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## What You Get

**Complete Observability Stack**
- Distributed tracing with Jaeger
- Advanced analytics with Kibana  
- Data persistence with Elasticsearch
- Real-time monitoring capabilities

**Production-Ready Code**
- 16 comprehensive test cases (77% coverage)
- Comprehensive error handling
- Docker containerization
- Load testing capabilities

**Developer Experience**  
- **Single-command setup**: `make full-setup`
- **Single-command demo**: `make demo`
- **Single-command cleanup**: `make full-stop`
- Comprehensive Makefile for all operations
- Clear troubleshooting with `make help`

This project demonstrates a complete, production-ready observability stack that can be adapted for any microservices architecture. **Everything is automated with make commands for the best developer experience!**

---

**TL;DR**: Run `make setup && make full-setup && make demo` for a complete working observability stack in 3 commands!