# E-commerce Microservices with Docker

This project demonstrates a complete microservices architecture for an e-commerce platform using FastAPI, Docker, PostgreSQL, Prometheus, and Grafana.

## Architecture Overview

The application is split into the following microservices:

- **API Gateway** (Port 8000): Routes requests to appropriate microservices
- **User Service** (Port 8001): User management and authentication
- **Product Service** (Port 8002): Product catalog management
- **Inventory Service** (Port 8003): Stock management and reservations
- **Order Service** (Port 8004): Order orchestration and workflow
- **Payment Service** (Port 8005): Payment processing
- **Notification Service** (Port 8006): Notification and messaging
- **PostgreSQL Database**: Shared database for all services
- **Prometheus** (Port 9090): Metrics collection
- **Grafana** (Port 3000): Metrics visualization

## Features

- **True Microservices Architecture**: Each service runs in its own Docker container
- **Database-backed operations** with PostgreSQL and async SQLAlchemy
- **API Gateway** for request routing and load balancing
- **Inter-service communication** via HTTP APIs
- **Comprehensive Prometheus metrics** for each microservice
- **Service discovery** and health checking
- **Centralized logging** and monitoring
- **Production-ready** Docker configuration

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available for containers
- Ports 8000-8006, 3000, 5432, and 9090 available

### Running the Microservices

1. **Start all services:**
   ```bash
   ./start-microservices.sh
   ```

2. **Or manually with docker-compose:**
   ```bash
   docker-compose -f docker-compose.microservices.yml up --build -d
   ```

3. **Check service health:**
   ```bash
   curl http://localhost:8000/health/services
   ```
<img width="907" height="825" alt="image" src="https://github.com/user-attachments/assets/0a07c525-730c-444d-bcbb-49c2e23db5ff" />

### Available Endpoints

#### API Gateway (Main Entry Point)
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Services Health**: http://localhost:8000/health/services

#### Individual Services
All services are accessible through the API Gateway at `/api/{service}/` or directly:

- **Users**: http://localhost:8000/api/users or http://localhost:8001/users
- **Products**: http://localhost:8000/api/products or http://localhost:8002/products
- **Inventory**: http://localhost:8000/api/inventory or http://localhost:8003/inventory
- **Orders**: http://localhost:8000/api/orders or http://localhost:8004/orders
- **Payments**: http://localhost:8000/api/payments or http://localhost:8005/payments
- **Notifications**: http://localhost:8000/api/notifications or http://localhost:8006/notifications

#### Monitoring
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
<img width="1901" height="898" alt="image" src="https://github.com/user-attachments/assets/66fd39aa-4549-48ce-ae32-d9def1acd129" />
<img width="1909" height="835" alt="image" src="https://github.com/user-attachments/assets/212181e7-7caf-4ff1-9ae3-3c1f11a6dd94" />

## API Examples

### Create a User
```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "name": "John Doe",
    "address": "123 Main St",
    "phone": "+1234567890"
  }'
```

### Create a Product
```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "category": "Electronics",
    "sku": "LAP001"
  }'
```

### Create an Order
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "unit_price": 999.99
      }
    ]
  }'
```

## Development

### Project Structure
```
microservices/
├── shared/                 # Shared modules and configurations
│   ├── config.py          # Service configurations
│   ├── database.py        # Database connection management
│   ├── models.py          # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── api-gateway/           # API Gateway service
├── user-service/          # User management service
├── product-service/       # Product catalog service
├── inventory-service/     # Inventory management service
├── order-service/         # Order orchestration service
├── payment-service/       # Payment processing service
└── notification-service/  # Notification service
```

### Adding a New Service

1. Create a new directory under `microservices/`
2. Create `main.py`, `requirements.txt`, and `Dockerfile`
3. Add service configuration to `shared/config.py`
4. Update `docker-compose.microservices.yml`
5. Add routing to API Gateway

### Environment Variables

Each service can be configured using environment variables:

- `ENVIRONMENT`: development/production
- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level
- `*_SERVICE_URL`: URLs for inter-service communication

## Monitoring and Metrics

### Prometheus Metrics

Each service exposes metrics at `/metrics`:

- **HTTP Request Metrics**: Request count, duration, status codes
- **Database Metrics**: Query performance, connection pool status
- **Business Metrics**: User count, order values, inventory levels
- **Service Health**: Uptime, error rates

### Grafana Dashboards

Pre-configured dashboards for:
- Service overview and health
- Request latency and throughput
- Database performance
- Business metrics

## Production Considerations

### Scaling

Scale individual services:
```bash
docker-compose -f docker-compose.microservices.yml up --scale user-service=3
```

### Load Balancing

The API Gateway handles load balancing. For production, consider:
- NGINX or HAProxy in front of API Gateway
- Multiple API Gateway instances
- Service mesh (Istio, Linkerd)

### Security

- Add authentication/authorization middleware
- Use HTTPS in production
- Implement rate limiting
- Network segmentation with Docker networks

### Database

- Use separate databases per service for true microservices
- Implement database migrations
- Add database monitoring and backups
- Consider read replicas for scaling

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000-8006, 3000, 5432, 9090 are available
2. **Memory issues**: Increase Docker memory allocation
3. **Service startup order**: Services depend on PostgreSQL being healthy

### Logs

View logs for specific services:
```bash
# All services
docker-compose -f docker-compose.microservices.yml logs -f

# Specific service
docker-compose -f docker-compose.microservices.yml logs -f user-service

# Follow logs in real-time
docker-compose -f docker-compose.microservices.yml logs -f --tail=100
```

### Health Checks

Check individual service health:
```bash
curl http://localhost:8001/health  # User service
curl http://localhost:8002/health  # Product service
# ... etc
```

## Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.microservices.yml down

# Stop and remove volumes (clears database)
docker-compose -f docker-compose.microservices.yml down -v

# Stop and remove images
docker-compose -f docker-compose.microservices.yml down --rmi all
```

## Migration from Monolith

The original monolithic application is still available in the `app/` directory. To migrate:

1. Both architectures share the same database schema
2. The API Gateway provides the same endpoints as the monolith
3. Metrics are collected from all services
4. Business logic remains the same, just distributed

## Contributing

1. Follow the existing service structure
2. Add comprehensive tests for new services
3. Update documentation
4. Ensure all services have proper health checks
5. Add appropriate metrics and logging
