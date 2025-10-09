#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test script for FastAPI Elasticsearch logging project
echo -e "${BLUE}FastAPI Elasticsearch Logging - Test Suite${NC}"
echo "=================================================="

# Function to check if services are running
check_services() {
    echo -e "\n${YELLOW}Checking if services are running...${NC}"
    
    # Check if containers are running
    if ! docker compose ps | grep -q "Up"; then
        echo -e "${RED}Error: Docker services are not running. Please run 'make full-setup' first.${NC}"
        exit 1
    fi
    
    # Check Elasticsearch
    echo "Checking Elasticsearch..."
    if curl -s -f http://localhost:9200/_cluster/health > /dev/null; then
        echo -e "${GREEN}✓ Elasticsearch is running${NC}"
    else
        echo -e "${RED}✗ Elasticsearch is not accessible${NC}"
        exit 1
    fi
    
    # Check Kibana
    echo "Checking Kibana..."
    if curl -s -f http://localhost:5601/api/status > /dev/null; then
        echo -e "${GREEN}✓ Kibana is running${NC}"
    else
        echo -e "${RED}✗ Kibana is not accessible${NC}"
        exit 1
    fi
    
    # Check FastAPI
    echo "Checking FastAPI..."
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ FastAPI is running${NC}"
    else
        echo -e "${RED}✗ FastAPI is not accessible${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All services are running!${NC}"
}

# Function to install test dependencies
install_deps() {
    echo -e "\n${YELLOW}Installing test dependencies...${NC}"
    if command -v uv &> /dev/null; then
        uv sync
    else
        echo -e "${RED}Error: uv not found. Please install uv first.${NC}"
        exit 1
    fi
}

# Function to run unit tests
run_unit_tests() {
    echo -e "\n${YELLOW}Running unit tests...${NC}"
    if uv run pytest tests/test_api.py tests/test_logging.py -v; then
        echo -e "${GREEN}✓ Unit tests passed${NC}"
    else
        echo -e "${RED}✗ Unit tests failed${NC}"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "\n${YELLOW}Running integration tests...${NC}"
    if uv run pytest tests/test_integration.py -v -m integration; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    echo -e "\n${YELLOW}Running all tests...${NC}"
    if uv run pytest tests/ -v; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        return 1
    fi
}

# Function to generate test report
generate_report() {
    echo -e "\n${YELLOW}Generating test coverage report...${NC}"
    uv run pytest tests/ --cov=app --cov-report=html --cov-report=term
    echo -e "${BLUE}Coverage report generated in htmlcov/index.html${NC}"
}

# Function to test logging manually
test_logging_manually() {
    echo -e "\n${YELLOW}Testing logging functionality manually...${NC}"
    
    echo "Making API requests to generate logs..."
    
    # Health check
    curl -s http://localhost:8000/health > /dev/null
    echo "✓ Health check request made"
    
    # Get users
    curl -s http://localhost:8000/api/v1/users > /dev/null
    echo "✓ Get users request made"
    
    # Create user
    curl -s -X POST http://localhost:8000/api/v1/users \
         -H "Content-Type: application/json" \
         -d '{"name": "Test User", "email": "test@example.com"}' > /dev/null
    echo "✓ Create user request made"
    
    # Get specific user (should cause 404)
    curl -s http://localhost:8000/api/v1/users/999 > /dev/null
    echo "✓ Get non-existent user request made (404)"
    
    echo -e "\n${BLUE}Waiting for logs to be indexed...${NC}"
    sleep 5
    
    # Check if logs exist in Elasticsearch
    echo "Checking logs in Elasticsearch..."
    if curl -s "http://localhost:9200/fastapi-logs-*/_search?size=5&sort=@timestamp:desc" | jq -r '.hits.total.value' > /dev/null 2>&1; then
        log_count=$(curl -s "http://localhost:9200/fastapi-logs-*/_search?size=0" | jq -r '.hits.total.value' 2>/dev/null || echo "0")
        echo -e "${GREEN}✓ Found $log_count logs in Elasticsearch${NC}"
    else
        echo -e "${YELLOW}Note: Could not verify logs in Elasticsearch (jq might not be installed)${NC}"
    fi
}

# Main function
main() {
    case "${1:-all}" in
        "services")
            check_services
            ;;
        "deps")
            install_deps
            ;;
        "unit")
            check_services
            install_deps
            run_unit_tests
            ;;
        "integration")
            check_services
            install_deps
            run_integration_tests
            ;;
        "manual")
            check_services
            test_logging_manually
            ;;
        "report")
            check_services
            install_deps
            generate_report
            ;;
        "all")
            check_services
            install_deps
            run_all_tests
            ;;
        *)
            echo "Usage: $0 [services|deps|unit|integration|manual|report|all]"
            echo ""
            echo "Commands:"
            echo "  services     - Check if all services are running"
            echo "  deps         - Install test dependencies"
            echo "  unit         - Run unit tests only"
            echo "  integration  - Run integration tests only"
            echo "  manual       - Test logging functionality manually"
            echo "  report       - Generate test coverage report"
            echo "  all          - Run all tests (default)"
            exit 1
            ;;
    esac
}

main "$@"