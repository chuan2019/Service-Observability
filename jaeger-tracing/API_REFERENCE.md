# FastAPI Jaeger Tracing Demo - API Reference

## Quick Access Links

- **Interactive API Docs (Swagger):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc  
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Jaeger Tracing UI:** http://localhost:16686

## Complete API Endpoints Reference

### Health & Status

#### Root Endpoint
```bash
curl http://localhost:8000/
```
**Response:**
```json
{
  "message": "FastAPI with Jaeger Tracing Demo",
  "status": "running"
}
```

#### Health Check
```bash
curl http://localhost:8000/health
```
**Response:**
```json
{
  "status": "healthy", 
  "service": "fastapi-jaeger-demo"
}
```

### User Management

#### Create User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com" 
  }'
```
**Response:**
```json
{
  "id": 1,
  "name": "John Doe", 
  "email": "john.doe@example.com",
  "status": "active"
}
```

#### Get User by ID
```bash
curl http://localhost:8000/users/{user_id}

# Example:
curl http://localhost:8000/users/1
```
**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com", 
  "status": "active"
}
```

### Order Management

#### Create Order
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "product": "Premium Widget",
    "amount": 99.99
  }'
```
**Response:**
```json
{
  "id": 101,
  "user_id": 1,
  "amount": 107.9892,
  "items": ["item1", "item2"],
  "status": "pending"
}
```

#### Get Order by ID
```bash
curl http://localhost:8000/orders/{order_id}

# Example:
curl http://localhost:8000/orders/101
```
**Response:**
```json
{
  "id": 101,
  "user_id": 1,
  "amount": 107.9892,
  "items": ["item1", "item2"],
  "status": "completed"
}
```

### Payment Processing

#### Process Payment
```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 99.99,
    "method": "credit_card"
  }'
```

**Supported Payment Methods:**
- `credit_card`
- `paypal`
- `stripe`
- `bank_transfer`

**Response:**
```json
{
  "id": 1001,
  "order_id": 101,
  "amount": 99.99,
  "method": "credit_card",
  "status": "success",
  "transaction_id": "txn_123456",
  "gateway_fee": 2.97,
  "processing_time": 0.234
}
```

### Demo Flow (Complete Transaction)

#### Full Flow Demo
```bash
curl http://localhost:8000/demo/full-flow/{user_id}

# Example:
curl http://localhost:8000/demo/full-flow/1
```

This endpoint demonstrates a complete transaction flow:
1. User lookup
2. Order creation
3. Payment processing
4. Full tracing across services

**Response:**
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "status": "active"
  },
  "order": {
    "id": 102,
    "user_id": 1,
    "amount": 107.99,
    "items": ["item1", "item2"],
    "status": "pending"
  },
  "payment": {
    "id": 1002,
    "order_id": 102,
    "amount": 107.99,
    "method": "credit_card",
    "status": "success",
    "transaction_id": "txn_789012",
    "gateway_fee": 3.13,
    "processing_time": 0.156
  },
  "flow_status": "completed"
}
```

## Testing Commands

### Quick Test All Endpoints
```bash
# Run comprehensive API test script
./scripts/test_api_endpoints.sh
```

### Individual Endpoint Testing
```bash
# Test user creation and retrieval
curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name":"Test User","email":"test@example.com"}'
curl http://localhost:8000/users/1

# Test order flow
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d '{"user_id":1,"product":"Test Product","amount":50.00}'
curl http://localhost:8000/orders/101

# Test complete flow with tracing
curl http://localhost:8000/demo/full-flow/1
```

## Monitoring & Observability

### View Traces
After making API calls, view the distributed traces:
1. Open Jaeger UI: http://localhost:16686
2. Select service: `fastapi-jaeger-demo`
3. Click "Find Traces"
4. Explore individual traces for timing details

### Check Service Health
```bash
# Development cluster status
make status-dev

# All services health check
make health
```

## Error Handling

### Common HTTP Status Codes
- `200` - Success
- `404` - Resource not found
- `422` - Validation error (invalid request data)
- `500` - Internal server error

### Example Error Response
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Performance Testing

### Load Testing
```bash
# Generate traffic for testing
make traffic-demo

# Run load tests
make load-test

# Heavy load testing  
make load-test-heavy
```

### Stress Testing
```bash
# Stress test with high RPS
make traffic-stress
```

All API calls are automatically traced and can be analyzed in the Jaeger UI for performance optimization and debugging!