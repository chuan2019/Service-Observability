# FastAPI + Jaeger + Kibana Observability Stack

A complete production-ready observability stack demonstrating distributed tracing with FastAPI, Jaeger, and Kibana integration.

## Features

- **FastAPI Application** with OpenTelemetry instrumentation
- **Distributed Tracing** with Jaeger using OTLP protocol  
- **Advanced Analytics** with Kibana and Elasticsearch
- **Comprehensive Testing** with pytest (16 test cases)
- **Traffic Generation** and load testing tools
- **Docker Compose** for easy deployment
- **Sample Data** and demonstration scripts

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

## Services

| Service | Port | Description |
|---------|------|-------------|
| **FastAPI** | 8000 | Main application with OpenTelemetry tracing |
| **Jaeger UI** | 16686 | Distributed tracing visualization |
| **Kibana** | 5601 | Advanced search and analytics |
| **Elasticsearch** | 9200 | Data storage and search engine |

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- UV package manager

## Quick Start

### 1. Clone and Setup

```bash
cd jaeger-tracing
uv sync
```

### 2. Start Infrastructure

```bash
# Start the complete observability stack
./scripts/start_full_stack.sh

# OR manually start individual services
docker-compose up -d elasticsearch kibana jaeger
```

### 3. Start FastAPI Application

```bash
# Method 1: Using the start script
./scripts/start_stack.sh

# Method 2: Manual start
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Run Integration Demo

```bash
./scripts/demo_integration.sh
```

## Service URLs

- **FastAPI Application**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

- **Jaeger UI**: http://localhost:16686
  - Service: `fastapi-jaeger-demo`

- **Kibana**: http://localhost:5601
  - Index Pattern: `jaeger-traces-demo*`

- **Elasticsearch**: http://localhost:9200

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
uv run pytest tests/test_main.py -v

# Run with coverage
uv run pytest tests/test_main.py --cov=app --cov-report=html

# Test specific functionality
uv run pytest tests/test_main.py::TestHealthEndpoint -v
```

## Generating Traffic

### Basic Traffic Generation

```bash
# Generate sample API calls
uv run python scripts/generate_traffic.py

# Run load test
uv run python scripts/load_test.py
```

### Create Demo Traces in Kibana

```bash
# Create sample trace data for Kibana analysis
uv run python scripts/create_demo_traces.py
```

## Kibana Integration

### Setting Up Kibana for Trace Analysis

1. **Access Kibana**: Visit http://localhost:5601

2. **Set Up Index Pattern**:
   - Go to **Stack Management** → **Index Patterns**
   - Select `jaeger-traces-demo*` index pattern
   - Set `timestamp` as the time field

3. **Explore Traces in Discover**:
   - Go to **Discover**
   - Select the `jaeger-traces-demo*` index pattern
   - Use time picker to filter by time range

### Sample Kibana Queries

```kuery
# Find all traces for a specific service
service: "fastapi-jaeger-demo"

# Find error traces
error: true

# Find slow operations (> 1 second)
duration_ms: >1000

# Find specific HTTP methods
method: "POST"

# Find specific status codes
status_code: 500

# Complex query: Find slow POST requests with errors
method: "POST" AND duration_ms: >500 AND error: true
```

### Creating Dashboards

You can create visualizations and dashboards for:
- **Response time trends**
- **Error rate by service**
- **Request volume over time**
- **Service dependency mapping**
- **Performance percentiles**

## Project Structure

```
jaeger-tracing/
├── app/                    # FastAPI application
│   ├── main.py            # Main application
│   ├── models.py          # Data models
│   └── routers/           # API route handlers
├── config/                # Configuration
│   └── tracing.py         # OpenTelemetry setup
├── tests/                 # Test suite
│   └── test_main.py       # Comprehensive tests
├── scripts/               # Utility scripts
│   ├── demo_integration.sh
│   ├── generate_traffic.py
│   ├── load_test.py
│   ├── create_demo_traces.py
│   └── setup_kibana.sh
├── kibana/                # Kibana configuration
├── docker-compose.yml     # Infrastructure setup
└── pyproject.toml         # Project dependencies
```

## Configuration

### OpenTelemetry Configuration

The tracing configuration is in `config/tracing.py`:

```python
# Key configuration
SERVICE_NAME = "fastapi-jaeger-demo"
JAEGER_ENDPOINT = "http://localhost:4318/v1/traces"  # OTLP HTTP
```

### Jaeger Configuration

Jaeger is configured to:
- Accept OTLP traces on port 4318
- Store data in Elasticsearch
- Provide UI on port 16686

### Kibana Configuration

Kibana is configured to:
- Connect to Elasticsearch
- Provide analytics UI on port 5601
- Support advanced trace queries

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/users` | GET | List users |
| `/users` | POST | Create user |
| `/users/{user_id}` | GET | Get user |
| `/orders` | POST | Create order |
| `/orders/{order_id}` | GET | Get order |
| `/payments` | POST | Process payment |
| `/demo/full-flow/{user_id}` | GET | Demonstrate full flow |

## Observability Features

### Distributed Tracing

The application creates detailed spans for:
- HTTP requests and responses
- Database operations (simulated)
- Business logic operations
- Error conditions and exceptions

### Custom Spans

Example of custom span creation:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("operation.type", "business_logic")
    # Your code here
```

## Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker is running and ports are available
2. **No traces in Jaeger**: Verify OTLP endpoint configuration
3. **Kibana not showing data**: Ensure Elasticsearch is running and index pattern is created

### Debugging Commands

```bash
# Check service status
curl http://localhost:8000/health
curl http://localhost:16686/api/services
curl http://localhost:5601/api/status

# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices

# View logs
docker-compose logs jaeger
docker-compose logs elasticsearch
docker-compose logs kibana
```

## Production Considerations

### Security
- Configure authentication for Kibana
- Secure Elasticsearch cluster
- Use HTTPS for all services
- Implement proper API keys

### Performance
- Configure sampling rates for high-traffic applications
- Set up proper Elasticsearch cluster sizing
- Monitor resource usage
- Implement retention policies

### Monitoring
- Set up alerts for trace errors
- Monitor service performance metrics
- Track system resource usage
- Configure backup strategies
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
## Advanced Kibana Analytics

### Dashboard Ideas
1. **Service Performance Dashboard**
   - Average response time by service
   - Request count over time
   - Error rate percentage

2. **Error Analysis Dashboard**
   - Top errors by service
   - Error trends over time
   - Error details and stack traces

3. **Business Metrics Dashboard**
   - User signup trends
   - Order completion rates
   - Payment success rates

### Alerting
Set up alerts in Kibana for:
- High error rates (> 5%)
- Slow responses (> 2 seconds)
- Service downtime
- Unusual traffic patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Documentation

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Features Demonstrated

**Complete Observability Stack**
- Distributed tracing with Jaeger
- Advanced analytics with Kibana
- Data persistence with Elasticsearch
- Real-time monitoring and alerting

**Production-Ready Code**
- Comprehensive error handling
- Proper logging and instrumentation
- Configuration management
- Docker containerization

**Testing & Validation**
- 16 comprehensive test cases
- Load testing capabilities
- Integration testing
- Health checks and monitoring

**Developer Experience**
- Easy setup and deployment
- Comprehensive documentation
- Utility scripts for common tasks
- Clear troubleshooting guides

This project demonstrates a complete, production-ready observability stack that can be adapted for any microservices architecture requiring distributed tracing and advanced analytics capabilities.