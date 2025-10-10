#!/bin/bash

# Complete stack startup script with proper service ordering
# This script starts the complete observability stack in the correct order

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

echo "FastAPI + Jaeger + Kibana + Elasticsearch Stack Startup"
echo "======================================================="
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Step 1: Clean up any existing containers
print_step "Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
print_success "Cleanup completed"

# Step 2: Start Elasticsearch first
print_step "Starting Elasticsearch..."
docker-compose up -d elasticsearch
echo "Waiting for Elasticsearch to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:9200/_cluster/health >/dev/null 2>&1; then
        print_success "Elasticsearch is ready"
        break
    fi
    echo -n "."
    sleep 2
    counter=$((counter + 2))
done
echo ""

if [ $counter -ge $timeout ]; then
    print_error "Elasticsearch failed to start within $timeout seconds"
    exit 1
fi

# Step 3: Start Kibana
print_step "Starting Kibana..."
docker-compose up -d kibana
echo "Waiting for Kibana to be ready..."
timeout=90
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:5601/api/status >/dev/null 2>&1; then
        print_success "Kibana is ready"
        break
    fi
    echo -n "."
    sleep 3
    counter=$((counter + 3))
done
echo ""

if [ $counter -ge $timeout ]; then
    print_warning "Kibana may not be fully ready, but continuing..."
fi

# Step 4: Start Jaeger with Elasticsearch backend
print_step "Starting Jaeger with Elasticsearch backend..."
docker-compose up -d jaeger
echo "Waiting for Jaeger to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:16686/ >/dev/null 2>&1; then
        print_success "Jaeger is ready"
        break
    fi
    echo -n "."
    sleep 2
    counter=$((counter + 2))
done
echo ""

if [ $counter -ge $timeout ]; then
    print_error "Jaeger failed to start within $timeout seconds"
    exit 1
fi

# Step 5: Optional - Start FastAPI services if requested
if [ "$1" = "--with-apps" ]; then
    print_step "Starting FastAPI applications..."
    docker-compose up -d fastapi-main fastapi-user-service fastapi-order-service fastapi-payment-service
    
    echo "Waiting for FastAPI services to be ready..."
    sleep 10
    
    services=("fastapi-main:8000" "fastapi-user-service:8001" "fastapi-order-service:8002" "fastapi-payment-service:8003")
    for service in "${services[@]}"; do
        name=${service%%:*}
        port=${service#*:}
        if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            print_success "$name is ready on port $port"
        else
            print_warning "$name may not be ready on port $port"
        fi
    done
fi

echo ""
print_success "Stack startup completed!"
echo ""
echo "Service URLs:"
echo "  - Elasticsearch: http://localhost:9200"
echo "  - Kibana: http://localhost:5601"
echo "  - Jaeger UI: http://localhost:16686"
if [ "$1" = "--with-apps" ]; then
    echo "  - FastAPI Main: http://localhost:8000"
    echo "  - FastAPI User Service: http://localhost:8001"
    echo "  - FastAPI Order Service: http://localhost:8002"
    echo "  - FastAPI Payment Service: http://localhost:8003"
fi
echo ""
echo "Next steps:"
echo "1. Start FastAPI application manually:"
echo "   uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "2. Or run the complete demo:"
echo "   ./scripts/demo_integration.sh"
echo ""
echo "3. Generate sample data:"
echo "   uv run python scripts/create_demo_traces.py"
echo ""
print_success "Ready to trace!"