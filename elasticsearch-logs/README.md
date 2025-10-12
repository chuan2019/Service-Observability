# FastAPI Elasticsearch Logging Demo

A comprehensive sample project demonstrating how to integrate Elasticsearch with a FastAPI application for centralized logging and monitoring. This project includes Docker containerization, uv for Python environment management, and Kibana for log visualization.

## Features

- **FastAPI Application**: Modern, fast API with comprehensive logging
- **Elasticsearch Integration**: Centralized log storage and indexing
- **Kibana Dashboard**: Log visualization and monitoring
- **Docker Compose**: Easy containerized deployment
- **uv Environment**: Modern Python package management
- **Structured Logging**: JSON-formatted logs with metadata
- **Health Checks**: Application and service monitoring
- **Sample Endpoints**: Users and Orders management APIs

## Project Structure

```
elasticsearch-logs/
├── app/                          # FastAPI application
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration settings
│   │   └── logging.py            # Elasticsearch logging setup
│   ├── routers/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py             # Health check endpoints
│   │   ├── users.py              # User management
│   │   └── orders.py             # Order management
│   └── services/                 # Business logic
│       └── __init__.py
├── config/                       # Configuration files
│   └── kibana.yml                # Kibana configuration
├── docker/                       # Docker files
│   └── Dockerfile                # FastAPI application container
├── scripts/                      # Utility scripts
│   ├── setup-kibana.sh           # Kibana setup automation
│   └── test-logging.sh           # Generate sample logs
├── docker-compose.yml            # Docker services definition
├── pyproject.toml                # Python project configuration
├── Makefile                      # Development commands
├── .env                          # Environment variables
└── README.md                     # This file
```

## Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **uv** (Python package manager)
- **curl** (for API testing)
- **jq** (for JSON formatting, optional)

### Install uv

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd elasticsearch-logs

# Complete setup (Docker + Dependencies + Kibana)
make full-setup
```

### 2. Start the FastAPI Application

```bash
# Start the FastAPI app in development mode
make run
```

### 3. Test the Integration

```bash
# Generate sample logs
./scripts/test-logging.sh
```

### 4. View Logs in Kibana

Open [http://localhost:5601](http://localhost:5601) and navigate to the **Discover** tab.

## Detailed Setup

### Manual Setup Steps

1. **Start Elasticsearch and Kibana**:
   ```bash
   make docker-up
   ```

2. **Install Dependencies**:
   ```bash
   make dev-install
   ```

3. **Setup Kibana**:
   ```bash
   make kibana-setup
   ```

4. **Run the Application**:
   ```bash
   make run
   ```

## Docker Development Environment

For a fully containerized development experience with live code reloading:

### Quick Start with Docker

```bash
# Start the complete development environment
./dev.sh start

# Or manually with docker-compose
docker-compose --profile dev up -d
```

### Docker Development Commands

| Command | Description |
|---------|-------------|
| `./dev.sh start` | Start development environment (ES + Kibana + FastAPI) |
| `./dev.sh stop` | Stop all services |
| `./dev.sh restart` | Restart all services |
| `./dev.sh logs` | Show logs for all services |
| `./dev.sh logs-app` | Show FastAPI app logs only |
| `./dev.sh build` | Build development Docker image |
| `./dev.sh shell` | Open shell in FastAPI container |
| `./dev.sh test` | Run tests in container |
| `./dev.sh status` | Show status of all services |
| `./dev.sh clean` | Clean up containers and volumes |

### Docker Development Features

- **Live Code Reloading**: Source code is mounted as volumes, changes reflect immediately
- **Isolated Environment**: Consistent development environment across machines
- **Full Stack**: Elasticsearch, Kibana, and FastAPI all running in containers
- **Volume Mounts**: Local code changes are reflected in the container
- **Separate Ports**: Development (8000) vs Production (8001) to avoid conflicts

### Development URLs (Docker)

- **FastAPI App**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Elasticsearch**: [http://localhost:9200](http://localhost:9200)
- **Kibana**: [http://localhost:5601](http://localhost:5601)

## Development Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install production dependencies |
| `make dev-install` | Install development dependencies |
| `make run` | Start FastAPI application |
| `make test` | Run tests with coverage |
| `make lint` | Run code linting |
| `make format` | Format code (black, isort, ruff) |
| `make docker-up` | Start Elasticsearch and Kibana |
| `make docker-down` | Stop all containers |
| `make docker-logs` | View container logs |
| `make kibana-setup` | Configure Kibana index patterns |
| `make full-setup` | Complete setup (Docker + Dependencies + Kibana) |
| `make full-stop` | Stop all services (Docker containers) |
| `make health-check` | Check service health |
| `make clean` | Clean temporary files |

## Service URLs

- **FastAPI Application**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Elasticsearch**: [http://localhost:9200](http://localhost:9200)
- **Kibana**: [http://localhost:5601](http://localhost:5601)

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service status

### Users Management
- `GET /api/v1/users` - List users (with pagination and filters)
- `GET /api/v1/users/{id}` - Get user by ID
- `POST /api/v1/users` - Create new user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Orders Management
- `GET /api/v1/orders` - List orders (with filters)
- `GET /api/v1/orders/{id}` - Get order by ID
- `POST /api/v1/orders` - Create new order
- `PUT /api/v1/orders/{id}` - Update order
- `DELETE /api/v1/orders/{id}` - Cancel order

## Kibana Setup

The project automatically configures Kibana with:

### Index Patterns
- **fastapi-logs-*** - Main log index pattern with @timestamp

### Saved Searches
- **FastAPI Error Logs** - Shows errors and warnings
- **FastAPI Request Logs** - HTTP request/response logs
- **User Activity Logs** - User and order activities

### Useful Kibana Queries

```
# Show only errors
level:ERROR

# Show completed requests
event:request_end

# Show failed HTTP requests
status_code:>=400

# Show slow requests (>1 second)
duration_seconds:>1

# Show logs for specific user
user_id:1

# Search in log messages
message:*exception*

# Show logs from specific endpoint
url:*/api/v1/users*

# Time range queries
@timestamp:[now-1h TO now]
```

## Testing

### Generate Sample Logs

```bash
# Generate various types of logs for testing
./scripts/test-logging.sh
```

### Run Unit Tests

```bash
# Run tests with coverage
make test

# Run specific test file
uv run pytest tests/test_main.py

# Run with verbose output
uv run pytest -v
```

## Log Structure

Each log entry includes:

```json
{
  "@timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.routers.users",
  "message": "User created successfully",
  "module": "users",
  "function": "create_user",
  "line": 123,
  "application": "FastAPI Elasticsearch Demo",
  "environment": "development",
  "event": "create_user_success",
  "user_id": 4,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "request_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Configuration

### Environment Variables

Copy `.env` file and modify as needed:

```bash
# Application settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
APP_NAME="FastAPI Elasticsearch Demo"

# Elasticsearch settings
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
ELASTICSEARCH_INDEX_PREFIX=fastapi-logs

# Kibana settings
KIBANA_HOST=localhost
KIBANA_PORT=5601
```

### Docker Configuration

The `docker-compose.yml` includes:
- **Elasticsearch 8.11.0** with security disabled for development
- **Kibana 8.11.0** connected to Elasticsearch
- **FastAPI app** (optional, for production deployment)

## Production Deployment

### Build and Deploy with Docker

```bash
# Build and start all services including FastAPI
make docker-up-all

# Or use docker-compose directly
docker-compose --profile production up -d
```

### Environment-specific Configuration

Create environment-specific `.env` files:
- `.env.development`
- `.env.staging`
- `.env.production`

## Security Considerations

### Development vs Production

**Development** (current setup):
- Elasticsearch security disabled
- No authentication required
- Debug logging enabled

**Production** (recommended changes):
- Enable Elasticsearch security
- Use authentication credentials
- Enable SSL/TLS
- Restrict network access
- Use secrets management

### Enable Security

1. Update `docker-compose.yml`:
   ```yaml
   elasticsearch:
     environment:
       - xpack.security.enabled=true
       - ELASTIC_PASSWORD=your-password
   ```

2. Update `.env`:
   ```bash
   ELASTICSEARCH_USERNAME=elastic
   ELASTICSEARCH_PASSWORD=your-password
   ELASTICSEARCH_USE_SSL=true
   ```

## Troubleshooting

### Common Issues

1. **Elasticsearch not starting**:
   ```bash
   # Check system requirements
   docker-compose logs elasticsearch
   
   # Increase virtual memory (Linux)
   sudo sysctl -w vm.max_map_count=262144
   ```

2. **Kibana connection issues**:
   ```bash
   # Check Elasticsearch health
   curl http://localhost:9200/_cluster/health
   
   # Restart Kibana
   docker-compose restart kibana
   ```

3. **FastAPI can't connect to Elasticsearch**:
   ```bash
   # Check if Elasticsearch is accessible
   curl http://localhost:9200
   
   # Check application logs
   make run
   ```

4. **Logs not appearing in Kibana**:
   - Verify index pattern: `fastapi-logs-*`
   - Check time range in Kibana
   - Refresh index pattern in Kibana Management

### Health Checks

```bash
# Check all services
make health-check

# Manual checks
curl http://localhost:9200/_cluster/health
curl http://localhost:5601/api/status
curl http://localhost:8000/health
```

## Cleanup

```bash
# Stop all services (quick cleanup)
make full-stop

# Stop containers (alternative)
make docker-down

# Remove volumes and clean up completely
make docker-clean

# Clean Python cache
make clean
```

## Testing

This project includes comprehensive test coverage for API endpoints, logging functionality, and Elasticsearch/Kibana integration.

### Test Categories

1. **Unit Tests** - Test individual components and functions
2. **Integration Tests** - Test service interactions (API ↔ Elasticsearch ↔ Kibana)
3. **Manual Tests** - Manual verification of logging workflow

### Prerequisites

Make sure all services are running before testing:

```bash
# Check if services are up
make test-services

# If not running, start them
make full-setup
```

### Running Tests

#### Run All Tests
```bash
# Run complete test suite
make test
```

#### Run Specific Test Categories
```bash
# Unit tests only (fast)
make test-unit

# Integration tests only (requires services)
make test-integration

# Manual logging test (generates actual logs)
make test-manual
```

#### Generate Test Coverage Report
```bash
# Generate detailed coverage report
make test-report

# View coverage report in browser
open htmlcov/index.html
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_api.py              # API endpoint tests
├── test_logging.py          # Logging functionality tests
└── test_integration.py      # End-to-end integration tests
```

### Key Test Features

#### API Testing
- Health endpoint validation
- User CRUD operations
- Order management
- Error handling (404, validation errors)
- Response format validation

#### Logging Tests
- Log configuration validation
- Request/response logging middleware
- Business logic logging
- Log structure and format verification
- Mock-based testing for isolation

#### Integration Tests
- Elasticsearch connectivity
- Log indexing and retrieval
- Kibana API interactions
- Index pattern creation
- End-to-end logging workflow
- Log correlation by request ID

### Test Configuration

Tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "integration: marks tests as integration tests",
]
```

### Manual Testing

For manual verification of the complete logging workflow:

```bash
# Run manual test (generates real logs and verifies)
make test-manual

# Or use the dedicated script
./scripts/test-logging.sh
```

This will:
1. Make various API requests
2. Generate logs with different levels
3. Wait for Elasticsearch indexing
4. Verify logs are searchable
5. Display log statistics

### Continuous Integration

The test suite is designed to work in CI environments:

```bash
# Install dependencies
uv sync

# Start services (in CI, use docker-compose)
docker-compose up -d

# Wait for services
sleep 30

# Run tests
uv run pytest tests/ --cov=app --cov-report=xml
```

### Test Coverage Goals

- **API Endpoints**: 100% coverage
- **Core Logic**: >95% coverage  
- **Integration Points**: All critical paths tested
- **Error Handling**: All error scenarios covered

### Troubleshooting Tests

#### Common Issues

1. **Services not running**:
   ```bash
   make test-services  # Check status
   make full-setup     # Start services
   ```

2. **Elasticsearch not ready**:
   ```bash
   # Wait longer for ES to start
   sleep 60
   curl http://localhost:9200/_cluster/health
   ```

3. **Test dependencies missing**:
   ```bash
   uv sync  # Install all dependencies
   ```

4. **Port conflicts**:
   ```bash
   # Check what's using the ports
   lsof -i :8000 -i :9200 -i :5601
   ```

#### Debugging Failed Tests

```bash
# Run tests with verbose output
uv run pytest tests/ -v -s

# Run specific test
uv run pytest tests/test_api.py::test_health_endpoint -v -s

# Run tests with debug info
uv run pytest tests/ --tb=long

# Skip integration tests if services unavailable
uv run pytest tests/ -m "not integration"
```

## Development Workflow

1. **Start development environment**:
   ```bash
   make dev
   ```

2. **Make code changes**
3. **Format and lint**:
   ```bash
   make format
   make lint
   ```

4. **Test**:
   ```bash
   make test
   ```

5. **Generate sample logs**:
   ```bash
   ./scripts/test-logging.sh
   ```

6. **View logs in Kibana**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make format && make lint && make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs: `make docker-logs`
3. Check service health: `make health-check`
4. Open an issue on GitHub

---

**Happy logging!**