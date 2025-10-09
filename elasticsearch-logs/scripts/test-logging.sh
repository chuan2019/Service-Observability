#!/bin/bash

# Test script to generate sample logs for testing Elasticsearch integration

set -e

API_BASE_URL="http://localhost:8000"

echo "Generating sample logs for testing..."
echo "API Base URL: $API_BASE_URL"

# Function to make API calls with error handling
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo "$description"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$API_BASE_URL$endpoint" \
             -H "Content-Type: application/json" \
             -d "$data" | jq '.' || echo "Request failed"
    else
        curl -s -X "$method" "$API_BASE_URL$endpoint" | jq '.' || echo "Request failed"
    fi
    
    sleep 1
}

# Check if API is running
echo "Checking if FastAPI is running..."
if ! curl -s "$API_BASE_URL/health" > /dev/null; then
    echo "FastAPI is not running. Please start it first with 'make run'"
    exit 1
fi

echo "FastAPI is running!"
echo ""

# Generate various types of logs
echo "Generating different types of logs..."
echo ""

# 1. Health checks
make_request "GET" "/health" "" "Health check"
make_request "GET" "/health/detailed" "" "Detailed health check"

# 2. User operations
make_request "GET" "/api/v1/users" "" "Get all users"
make_request "GET" "/api/v1/users/1" "" "Get user by ID"
make_request "POST" "/api/v1/users" '{"name": "Test User", "email": "test@example.com"}' "Create new user"
make_request "GET" "/api/v1/users?active_only=false&limit=5" "" "Get users with filters"

# 3. Order operations
make_request "GET" "/api/v1/orders" "" "Get all orders"
make_request "GET" "/api/v1/orders/1" "" "Get order by ID"
make_request "POST" "/api/v1/orders" '{"user_id": 1, "product_name": "Test Product", "quantity": 2, "price": 29.99}' "Create new order"
make_request "PUT" "/api/v1/orders/1" '{"status": "processing"}' "Update order status"

# 4. Generate some errors
echo ""
echo "Generating error logs..."
make_request "GET" "/api/v1/users/999" "" "Try to get non-existent user (404 error)"
make_request "GET" "/api/v1/orders/999" "" "Try to get non-existent order (404 error)"
make_request "POST" "/api/v1/users" '{"name": "Test User", "email": "invalid-email"}' "Try to create user with invalid email"

# 5. Generate high-volume requests for performance testing
echo ""
echo "Generating high-volume requests..."
for i in {1..10}; do
    make_request "GET" "/api/v1/users" "" "Bulk request $i/10" &
done
wait

# 6. Test different query parameters
echo ""
echo "Testing various query parameters..."
make_request "GET" "/api/v1/users?skip=0&limit=2" "" "Paginated users request"
make_request "GET" "/api/v1/orders?status=pending" "" "Filter orders by status"
make_request "GET" "/api/v1/orders?user_id=1" "" "Filter orders by user"

echo ""
echo "Sample log generation complete!"
echo ""
echo "You should now see logs in:"
echo "  - Console output"
echo "  - logs/app.log file"
echo "  - Elasticsearch (if running)"
echo "  - Kibana Discover tab"
echo ""
echo "Useful links:"
echo "  - FastAPI Docs: http://localhost:8000/docs"
echo "  - Kibana: http://localhost:5601"
echo "  - Elasticsearch: http://localhost:9200"