#!/bin/bash

# Microservices deployment script
set -e

echo "Starting E-commerce Microservices Deployment"
echo "============================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Build and start microservices
echo "Building and starting microservices..."
docker-compose -f docker-compose.microservices.yml up --build -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check service health
echo "Checking service health..."
services=("postgres:5432" "api-gateway:8000" "user-service:8001" "product-service:8002" "inventory-service:8003" "order-service:8004" "payment-service:8005" "notification-service:8006")

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    echo "Checking $service_name..."
    docker-compose -f docker-compose.microservices.yml exec -T $service_name curl -f http://localhost:$(echo $service | cut -d: -f2)/health >/dev/null 2>&1 && echo "✅ $service_name is healthy" || echo "❌ $service_name is not healthy"
done

echo ""
echo "🚀 Microservices are starting up!"
echo ""
echo "Available services:"
echo "📊 API Gateway:        http://localhost:8000"
echo "👥 User Service:       http://localhost:8001"
echo "📦 Product Service:    http://localhost:8002"
echo "📊 Inventory Service:  http://localhost:8003"
echo "🛒 Order Service:      http://localhost:8004"
echo "💳 Payment Service:    http://localhost:8005"
echo "📧 Notification Service: http://localhost:8006"
echo ""
echo "Monitoring:"
echo "📈 Prometheus:         http://localhost:9090"
echo "📊 Grafana:           http://localhost:3000 (admin:admin123)"
echo ""
echo "API Documentation:"
echo "📚 API Gateway Docs:   http://localhost:8000/docs"
echo ""
echo "Health Check:"
echo "🏥 Services Health:    http://localhost:8000/health/services"
echo ""
echo "To view logs: docker-compose -f docker-compose.microservices.yml logs -f [service-name]"
echo "To stop: docker-compose -f docker-compose.microservices.yml down"