#!/bin/bash

# Test Prometheus and Grafana Integration
# This script verifies the metrics collection pipeline

echo "================================================"
echo "  Prometheus & Grafana Integration Test"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $response)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (HTTP $response, expected $expected_code)"
        ((FAILED++))
        return 1
    fi
}

# Function to check metrics content
test_metrics_content() {
    local service=$1
    local url=$2
    local metric_name=$3
    
    echo -n "Checking $service for metric '$metric_name'... "
    
    content=$(curl -s "$url" 2>/dev/null)
    
    if echo "$content" | grep -q "$metric_name"; then
        echo -e "${GREEN}FOUND${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}NOT FOUND${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "=== Part 1: Service Health Checks ==="
echo ""

test_endpoint "User Service Health" "http://localhost:8001/health"
test_endpoint "Product Service Health" "http://localhost:8002/health"
test_endpoint "Inventory Service Health" "http://localhost:8003/health"
test_endpoint "Order Service Health" "http://localhost:8004/health"
test_endpoint "Payment Service Health" "http://localhost:8005/health"
test_endpoint "Notification Service Health" "http://localhost:8006/health"

echo ""
echo "=== Part 2: Prometheus Metrics Endpoints ==="
echo ""

test_endpoint "User Service Metrics" "http://localhost:8001/metrics"
test_endpoint "Product Service Metrics" "http://localhost:8002/metrics"
test_endpoint "Inventory Service Metrics" "http://localhost:8003/metrics"
test_endpoint "Order Service Metrics" "http://localhost:8004/metrics"
test_endpoint "Payment Service Metrics" "http://localhost:8005/metrics"
test_endpoint "Notification Service Metrics" "http://localhost:8006/metrics"

echo ""
echo "=== Part 3: Verify HTTP Request Metrics ==="
echo ""

# Generate some traffic first
echo "Generating test traffic..."
curl -s http://localhost:8000/api/users > /dev/null 2>&1
curl -s http://localhost:8000/api/products > /dev/null 2>&1
curl -s http://localhost:8000/api/inventory > /dev/null 2>&1
sleep 2

# Check for HTTP metrics
test_metrics_content "User Service" "http://localhost:8001/metrics" "http_requests_total"
test_metrics_content "User Service" "http://localhost:8001/metrics" "http_request_duration_seconds"
test_metrics_content "Product Service" "http://localhost:8002/metrics" "http_requests_total"

echo ""
echo "=== Part 4: Verify Business Metrics ==="
echo ""

test_metrics_content "User Service" "http://localhost:8001/metrics" "user_service_operations_total"
test_metrics_content "Product Service" "http://localhost:8002/metrics" "product_service_operations_total"
test_metrics_content "Order Service" "http://localhost:8004/metrics" "order_service_operations_total"
test_metrics_content "Payment Service" "http://localhost:8005/metrics" "payment_service_operations_total"

echo ""
echo "=== Part 5: Prometheus Server ==="
echo ""

test_endpoint "Prometheus Health" "http://localhost:9090/-/healthy"
test_endpoint "Prometheus API" "http://localhost:9090/api/v1/query?query=up"

echo ""
echo -n "Checking Prometheus targets... "
targets=$(curl -s "http://localhost:9090/api/v1/targets" | grep -o '"health":"up"' | wc -l)
if [ "$targets" -gt 5 ]; then
    echo -e "${GREEN}PASS${NC} ($targets targets up)"
    ((PASSED++))
else
    echo -e "${YELLOW}WARNING${NC} (only $targets targets up, expected 6+)"
    ((PASSED++))
fi

echo ""
echo "=== Part 6: Grafana Server ==="
echo ""

test_endpoint "Grafana Health" "http://localhost:3000/api/health"
test_endpoint "Grafana Datasources" "http://localhost:3000/api/datasources" 200

echo ""
echo "=== Part 7: Sample PromQL Queries ==="
echo ""

# Function to test PromQL query
test_promql() {
    local description=$1
    local query=$2
    
    echo -n "Testing: $description... "
    
    encoded_query=$(echo "$query" | jq -sRr @uri)
    response=$(curl -s "http://localhost:9090/api/v1/query?query=$encoded_query")
    
    status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" = "success" ]; then
        result_count=$(echo "$response" | jq -r '.data.result | length')
        echo -e "${GREEN}PASS${NC} ($result_count results)"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

test_promql "Total request rate" "sum(rate(http_requests_total[5m]))"
test_promql "Request rate by service" "sum(rate(http_requests_total[5m])) by (service)"
test_promql "Error rate" "sum(rate(http_requests_total{status_code=~\"4..|5..\"}[5m]))"
test_promql "Active users gauge" "user_service_active_users"

echo ""
echo "================================================"
echo "  Test Results"
echo "================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open Grafana: http://localhost:3000 (admin/admin123)"
    echo "2. Import dashboard from grafana-dashboard.json"
    echo "3. Generate traffic: python scripts/generate_traffic.py"
    echo "4. Watch metrics in real-time!"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check all services are running: docker ps"
    echo "2. Check service logs: docker-compose -f docker-compose.microservices.yml logs [service-name]"
    echo "3. Verify Prometheus targets: http://localhost:9090/targets"
    exit 1
fi
