# FastAPI Prometheus & Grafana Integration Guide

This document explains how the microservices architecture integrates with Prometheus for metrics collection and Grafana for visualization.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Metrics Collection Flow                       │
└─────────────────────────────────────────────────────────────────┘

  FastAPI Services                Prometheus              Grafana
┌──────────────────┐           ┌──────────────┐      ┌─────────────┐
│ User Service     │◄─scrape──┤              │      │             │
│ :8001/metrics    │           │  Prometheus  │◄─────┤   Grafana   │
├──────────────────┤           │   :9090      │query │   :3000     │
│ Product Service  │◄─scrape──┤              │      │             │
│ :8002/metrics    │           │  Time-Series │      │ Dashboards  │
├──────────────────┤           │   Database   │      │ & Alerts    │
│ Inventory Service│◄─scrape──┤              │      │             │
│ :8003/metrics    │           └──────────────┘      └─────────────┘
├──────────────────┤                  ▲
│ Order Service    │◄─scrape──────────┘
│ :8004/metrics    │
├──────────────────┤
│ Payment Service  │◄─scrape──────────┐
│ :8005/metrics    │                  │
├──────────────────┤                  │
│ Notification Svc │◄─scrape──────────┘
│ :8006/metrics    │
└──────────────────┘
```

## Integration Components

### 1. **FastAPI Application Instrumentation**

Each microservice is instrumented with Prometheus metrics using the `prometheus_client` library.

#### Installation
```bash
pip install prometheus-client
```

#### Code Implementation

**Step 1: Import Prometheus Client**
```python
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge, REGISTRY
```

**Step 2: Define Metrics**
```python
# Business Metrics (Service-Specific)
USER_OPERATIONS = Counter(
    'user_service_operations_total',
    'Total user service operations',
    ['operation', 'status'],  # Labels for filtering
    registry=REGISTRY
)

USER_OPERATION_DURATION = Histogram(
    'user_service_operation_duration_seconds',
    'User service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_USERS = Gauge(
    'user_service_active_users',
    'Number of active users',
    registry=REGISTRY
)
```

**Step 3: Mount Metrics Endpoint**
```python
app = FastAPI(title="User Service")

# Create Prometheus ASGI app
metrics_app = make_asgi_app(registry=REGISTRY)

# Mount at /metrics endpoint
app.mount("/metrics", metrics_app)
```

**Step 4: Add Metrics Middleware**
```python
from shared.middleware import PrometheusMiddleware

# Add after creating FastAPI app
app.add_middleware(PrometheusMiddleware, service_name="user-service")
```

This middleware automatically tracks:
- **HTTP request count** by method, endpoint, status code
- **HTTP request duration** (latency) with percentiles
- **HTTP requests in progress** (concurrent requests)

**Step 5: Instrument Business Logic**
```python
@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    """Create a new user."""
    start_time = time.time()
    
    try:
        # Business logic
        db_user = User(**user.model_dump())
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        
        # Track successful operation
        USER_OPERATIONS.labels(operation="create", status="success").inc()
        ACTIVE_USERS.inc()
        
        return UserResponse.model_validate(db_user)
    
    except Exception as e:
        # Track failed operation
        USER_OPERATIONS.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Track operation duration
        duration = time.time() - start_time
        USER_OPERATION_DURATION.labels(operation="create").observe(duration)
```

### 2. **Prometheus Configuration**

Prometheus is configured to scrape metrics from all microservices.

**File:** `config/prometheus-microservices.yml`

```yaml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate rules

scrape_configs:
  # User Service
  - job_name: 'user-service'
    static_configs:
      - targets: ['user-service:8001']
    metrics_path: '/metrics'  # Where to scrape from
    scrape_interval: 5s       # Override global interval
  
  # Product Service
  - job_name: 'product-service'
    static_configs:
      - targets: ['product-service:8002']
    metrics_path: '/metrics'
    scrape_interval: 5s
  
  # ... (other services)
```

**Key Parameters:**
- `scrape_interval`: How frequently Prometheus collects metrics
- `metrics_path`: The endpoint exposing Prometheus metrics
- `targets`: Service hostname and port
- `job_name`: Label to identify the service in Prometheus

### 3. **Docker Compose Integration**

**File:** `docker-compose.microservices.yml`

```yaml
services:
  # Prometheus
  prometheus:
    image: prom/prometheus:v2.47.0
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus-microservices.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - microservices
    depends_on:
      - api-gateway

  # Grafana
  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - microservices

volumes:
  prometheus_data:
  grafana_data:

networks:
  microservices:
    driver: bridge
```

### 4. **Grafana Data Source Configuration**

**File:** `config/grafana/datasources/prometheus.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090  # Prometheus service URL
    isDefault: true
    editable: true
```

This configures Grafana to automatically connect to Prometheus as its data source.

### 5. **Grafana Dashboard Provisioning**

**File:** `config/grafana/dashboards/dashboard.yml`

```yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Metric Types Explained

### 1. **Counter** - Monotonically Increasing Value
```python
USER_OPERATIONS = Counter('user_operations_total', 'Total operations', ['operation', 'status'])

# Usage
USER_OPERATIONS.labels(operation="create", status="success").inc()
```

**Use Cases:**
- Total requests
- Total errors
- Total operations completed

**PromQL Queries:**
```promql
# Rate of operations per second
rate(user_operations_total[5m])

# Total operations in last hour
sum(increase(user_operations_total[1h]))
```

### 2. **Histogram** - Distribution of Values
```python
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Request duration',
    ['endpoint'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0)
)

# Usage
REQUEST_DURATION.labels(endpoint="/api/users").observe(0.125)
```

**Use Cases:**
- Request latency
- Response time
- Operation duration

**PromQL Queries:**
```promql
# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 50th percentile (median)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### 3. **Gauge** - Value That Can Go Up or Down
```python
ACTIVE_USERS = Gauge('active_users', 'Current active users')

# Usage
ACTIVE_USERS.inc()      # Increment by 1
ACTIVE_USERS.dec()      # Decrement by 1
ACTIVE_USERS.set(100)   # Set to specific value
```

**Use Cases:**
- Current connections
- Queue length
- Memory usage
- Temperature

**PromQL Queries:**
```promql
# Current value
active_users

# Average over time
avg_over_time(active_users[5m])
```

## Common PromQL Queries for Dashboard

### Request Rate
```promql
# Total request rate across all services
sum(rate(http_requests_total[5m]))

# Request rate by service
sum(rate(http_requests_total[5m])) by (service)

# Request rate by endpoint
sum(rate(http_requests_total[5m])) by (endpoint, service)
```

### Error Rate
```promql
# Error rate (4xx and 5xx)
sum(rate(http_requests_total{status_code=~"4..|5.."}[5m]))

# Error rate by service
sum(rate(http_requests_total{status_code=~"4..|5.."}[5m])) by (service)

# Error percentage
(sum(rate(http_requests_total{status_code=~"4..|5.."}[5m])) / 
 sum(rate(http_requests_total[5m]))) * 100
```

### Response Time
```promql
# 95th percentile latency by service
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))

# Median latency
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))

# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Status Codes
```promql
# Requests by status code
sum(rate(http_requests_total[5m])) by (status_code, service)

# Success rate (2xx)
sum(rate(http_requests_total{status_code=~"2.."}[5m]))
```

### Business Metrics
```promql
# User operations rate
sum(rate(user_operations_total[5m])) by (operation)

# Product operations rate
sum(rate(product_operations_total[5m])) by (operation)

# Order operations rate
sum(rate(order_operations_total[5m])) by (operation)

# Payment operations rate
sum(rate(payment_operations_total[5m])) by (operation)
```

## Testing the Integration

### 1. **Start the Stack**
```bash
./start-microservices.sh
```

### 2. **Verify Metrics Endpoints**
```bash
# Check user service metrics
curl http://localhost:8001/metrics

# Check product service metrics
curl http://localhost:8002/metrics

# You should see output like:
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
# http_requests_total{endpoint="/api/users",method="GET",service="user-service",status_code="200"} 42.0
```

### 3. **Access Prometheus**
- URL: http://localhost:9090
- Go to Status → Targets to verify all services are being scraped
- Go to Graph and try queries:
  ```promql
  rate(http_requests_total[5m])
  ```

### 4. **Access Grafana**
- URL: http://localhost:3000
- Login: admin / admin123
- Go to Dashboards → Import
- Upload `grafana-dashboard.json`
- Select "Prometheus" as datasource

### 5. **Generate Traffic**
```bash
# Run traffic generator
python scripts/generate_traffic.py

# Or run load test
python scripts/load_test.py
```

## Key Benefits

1. **Automatic HTTP Metrics**: Middleware tracks all requests automatically
2. **Custom Business Metrics**: Track domain-specific operations
3. **Real-Time Monitoring**: See metrics with 5-second refresh
4. **Historical Analysis**: Prometheus stores data for analysis
5. **Alerting**: Configure alerts in Grafana for anomalies
6. **Service Health**: Monitor service availability and performance

## Best Practices

1. **Label Cardinality**: Keep labels low-cardinality (avoid user IDs, timestamps)
   ```python
   # Good
   REQUESTS.labels(endpoint="/api/users", method="GET")
   
   # Bad - will create millions of time series
   REQUESTS.labels(endpoint=f"/api/users/{user_id}")
   ```

2. **Metric Naming**: Follow Prometheus conventions
   ```
   <namespace>_<name>_<unit>_total
   
   Examples:
   - http_requests_total
   - http_request_duration_seconds
   - user_operations_total
   ```

3. **Use Appropriate Metric Types**:
   - Counter: Things that only increase (requests, errors, operations)
   - Gauge: Values that fluctuate (connections, memory, queue size)
   - Histogram: Distribution of values (latency, response time)

4. **Avoid Metrics Explosion**: Don't create metrics in loops
   ```python
   # Bad - creates new metric for each user
   for user in users:
       Counter(f'user_{user.id}_requests').inc()
   
   # Good - uses labels
   USER_REQUESTS.labels(user_type=user.type).inc()
   ```

5. **Monitor What Matters**:
   - **RED Method** (for requests): Rate, Errors, Duration
   - **USE Method** (for resources): Utilization, Saturation, Errors
   - **Business Metrics**: Domain-specific KPIs

## Troubleshooting

### Metrics Not Appearing in Prometheus
1. Check service is running: `docker ps`
2. Check service logs: `docker logs <service-name>`
3. Verify /metrics endpoint: `curl http://localhost:8001/metrics`
4. Check Prometheus targets: http://localhost:9090/targets
5. Verify network connectivity in Docker Compose

### Grafana Not Showing Data
1. Verify Prometheus datasource is configured
2. Check datasource health in Grafana settings
3. Test PromQL query directly in Prometheus
4. Verify time range in Grafana dashboard

### High Memory Usage
1. Reduce metric cardinality (fewer label combinations)
2. Adjust Prometheus retention time
3. Use recording rules for expensive queries

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
