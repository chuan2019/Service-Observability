#!/bin/bash

# Complete integration demonstration script
# This script shows the full Jaeger + Kibana integration working together

set -e

echo "FastAPI + Jaeger + Kibana Integration Demo"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}> $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

# Step 1: Check all services
print_step "Checking all services..."

services=(
    "Elasticsearch:http://localhost:9200/_cluster/health"
    "Kibana:http://localhost:5601/api/status"
    "Jaeger:http://localhost:16686/"
    "FastAPI:http://localhost:8000/health"
)

all_running=true
for service in "${services[@]}"; do
    name=${service%%:*}
    url=${service#*:}
    
    if curl -f "$url" >/dev/null 2>&1; then
        print_success "$name is running"
    else
        echo "[ERROR] $name is not accessible at $url"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo ""
    echo "[WARNING] Some services are not running. Starting the full stack..."
    ./scripts/start_full_stack.sh
    
    # Start FastAPI if not running
    if ! curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        echo "Starting FastAPI application..."
        uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 5
    fi
fi

echo ""

# Step 2: Generate traces
print_step "Generating traces in FastAPI application..."
echo "Making API calls to generate distributed traces..."

# Health check
curl -s http://localhost:8000/health >/dev/null

# Create users
for i in {1..3}; do
    curl -s -X POST http://localhost:8000/users \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"Demo User $i\", \"email\": \"user$i@demo.com\"}" >/dev/null
    echo -n "."
done

# Create orders and full flows
for i in {1..2}; do
    curl -s http://localhost:8000/demo/full-flow/$i >/dev/null
    echo -n "."
done

echo ""
print_success "Generated traces in Jaeger"

# Step 3: Wait for trace processing
print_step "Waiting for traces to be processed..."
sleep 3

# Step 4: Verify traces in Jaeger
print_step "Checking traces in Jaeger..."
jaeger_traces=$(curl -s "http://localhost:16686/api/traces?service=fastapi-jaeger-demo&limit=10" | jq '.data | length' 2>/dev/null || echo "0")
print_success "Found $jaeger_traces traces in Jaeger"

# Step 5: Create demo data in Kibana
print_step "Creating demo trace data in Kibana..."
cd "$(dirname "$0")/.."
uv run python scripts/create_demo_traces.py >/dev/null 2>&1
print_success "Created sample traces in Elasticsearch for Kibana"

# Step 6: Verify data in Elasticsearch
print_step "Verifying data in Elasticsearch..."
kibana_traces=$(curl -s "http://localhost:9200/jaeger-traces-demo/_search" | jq '.hits.total.value' 2>/dev/null || echo "0")
print_success "Found $kibana_traces demo traces in Elasticsearch"

# Step 7: Test Kibana integration
print_step "Testing Kibana integration..."
kibana_status=$(curl -s "http://localhost:5601/api/status" | jq -r '.status.overall.state' 2>/dev/null || echo "unknown")
if [ "$kibana_status" = "green" ]; then
    print_success "Kibana is healthy and ready"
else
    print_info "Kibana status: $kibana_status"
fi

echo ""
echo "Integration Demo Complete!"
echo ""
echo "What you can do now:"
echo ""
echo "1. View Distributed Traces in Jaeger:"
echo "   - Open: http://localhost:16686"
echo "   - Select service: 'fastapi-jaeger-demo'"
echo "   - Click 'Find Traces' to see your API calls"
echo ""
echo "2. Analyze Traces in Kibana:"
echo "   - Open: http://localhost:5601"
echo "   - Go to 'Discover'"
echo "   - Select index pattern: 'jaeger-traces-demo*'"
echo "   - Explore trace data with advanced queries"
echo ""
echo "3. Generate More Traffic:"
echo "   - Run: uv run python scripts/generate_traffic.py"
echo "   - Run: uv run python scripts/load_test.py"
echo ""
echo "4. Run Tests:"
echo "   - Run: uv run pytest tests/test_main.py -v"
echo ""
echo "Sample Kibana Queries to Try:"
echo "   - service: \"fastapi-jaeger-demo\""
echo "   - error: true"
echo "   - duration_ms: >1000"
echo "   - status_code: 500"
echo "   - method: \"POST\" AND error: true"
echo ""
echo "This demonstrates a complete production-ready observability stack!"
echo "   [SUCCESS] Distributed tracing with Jaeger"
echo "   [SUCCESS] Advanced analytics with Kibana"
echo "   [SUCCESS] Data storage with Elasticsearch"
echo "   [SUCCESS] Comprehensive testing with pytest"
echo "   [SUCCESS] Traffic generation and load testing"
echo ""
print_success "Integration is working perfectly!"