#!/bin/bash
# Comprehensive API Testing Script
# Tests all FastAPI endpoints with curl commands

echo "=== FastAPI Jaeger Tracing Demo - API Testing ==="
echo "Base URL: http://localhost:8000"
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to make API calls and display results
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${BLUE}### $description${NC}"
    echo "Command: curl -X $method http://localhost:8000$endpoint"
    if [ ! -z "$data" ]; then
        echo "Data: $data"
        echo ""
        response=$(curl -s -X $method -H "Content-Type: application/json" -d "$data" "http://localhost:8000$endpoint")
    else
        echo ""
        response=$(curl -s -X $method "http://localhost:8000$endpoint")
    fi
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}Response:${NC}"
        echo "$response" | jq
    else
        echo -e "${RED}Response (non-JSON):${NC}"
        echo "$response"
    fi
    echo ""
    echo "---"
    echo ""
}

# Test all endpoints
echo "HEALTH & STATUS ENDPOINTS"
test_endpoint "GET" "/" "" "Root endpoint"
test_endpoint "GET" "/health" "" "Health check"

echo ""
echo "USER MANAGEMENT ENDPOINTS"
test_endpoint "POST" "/users" '{"name":"Alice Johnson","email":"alice@example.com"}' "Create user - Alice"
test_endpoint "POST" "/users" '{"name":"Bob Smith","email":"bob@example.com"}' "Create user - Bob"
test_endpoint "GET" "/users/1" "" "Get user by ID (1)"
test_endpoint "GET" "/users/2" "" "Get user by ID (2)"

echo ""
echo "ORDER MANAGEMENT ENDPOINTS"
test_endpoint "POST" "/orders" '{"user_id":1,"product":"Laptop","amount":999.99}' "Create order - Laptop"
test_endpoint "POST" "/orders" '{"user_id":2,"product":"Mouse","amount":29.99}' "Create order - Mouse"
test_endpoint "GET" "/orders/101" "" "Get order by ID (101)"
test_endpoint "GET" "/orders/102" "" "Get order by ID (102)"

echo ""
echo "PAYMENT PROCESSING ENDPOINTS"
test_endpoint "POST" "/payments" '{"amount":999.99,"method":"credit_card"}' "Process payment - Credit Card"
test_endpoint "POST" "/payments" '{"amount":29.99,"method":"paypal"}' "Process payment - PayPal"

echo ""
echo "DEMO FLOW ENDPOINTS"
test_endpoint "GET" "/demo/full-flow/1" "" "Demo full flow for user 1"
test_endpoint "GET" "/demo/full-flow/2" "" "Demo full flow for user 2"

echo ""
echo "=== API Testing Complete ==="
echo ""
echo "Check traces in Jaeger UI: http://localhost:16686"
echo "View API docs at: http://localhost:8000/docs"
echo "Alternative docs: http://localhost:8000/redoc"