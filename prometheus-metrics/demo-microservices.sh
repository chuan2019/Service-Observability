#!/bin/bash

# Simple microservices demo - start core services only
set -e

echo "Starting Core Microservices Demo"
echo "================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

echo "Starting PostgreSQL and core services..."

# Start PostgreSQL first
docker-compose -f docker-compose.microservices.yml up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Start User and Product services
docker-compose -f docker-compose.microservices.yml up -d user-service product-service

echo "Waiting for services to start..."
sleep 15

# Start API Gateway
docker-compose -f docker-compose.microservices.yml up -d api-gateway

echo "Waiting for API Gateway..."
sleep 10

echo ""
echo "🚀 Core microservices are running!"
echo ""
echo "Available services:"
echo "📊 API Gateway:        http://localhost:8000"
echo "👥 User Service:       http://localhost:8001"
echo "📦 Product Service:    http://localhost:8002"
echo "🗄️  PostgreSQL:        localhost:5432"
echo ""
echo "API Documentation:"
echo "📚 API Gateway Docs:   http://localhost:8000/docs"
echo ""
echo "Health Check:"
echo "🏥 API Gateway Health: http://localhost:8000/health"
echo "🏥 Services Health:    http://localhost:8000/health/services"
echo ""
echo "Test the services:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:8001/health"
echo "curl http://localhost:8002/health"
echo ""
echo "To view logs: docker-compose -f docker-compose.microservices.yml logs -f [service-name]"
echo "To stop: docker-compose -f docker-compose.microservices.yml down"