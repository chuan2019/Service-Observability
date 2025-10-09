#!/bin/bash
# Setup script for FastAPI Jaeger Tracing Demo

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================${NC}"
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
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check Python
    if command_exists python3; then
        print_success "Python 3 is installed ($(python3 --version))"
    else
        print_error "Python 3 is not installed"
        missing_deps+=("python3")
    fi
    
    # Check UV
    if command_exists uv; then
        print_success "UV is installed ($(uv --version))"
    else
        print_warning "UV is not installed. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
        if command_exists uv; then
            print_success "UV installed successfully"
        else
            print_error "Failed to install UV"
            missing_deps+=("uv")
        fi
    fi
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker is installed ($(docker --version))"
    else
        print_warning "Docker is not installed (optional for local development)"
    fi
    
    # Check Docker Compose
    if command_exists docker-compose; then
        print_success "Docker Compose is installed ($(docker-compose --version))"
    elif command_exists docker && docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose is available via docker compose"
    else
        print_warning "Docker Compose is not available (optional for container deployment)"
    fi
    
    # Check curl
    if command_exists curl; then
        print_success "curl is installed"
    else
        print_warning "curl is not installed (needed for health checks)"
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Please install the missing dependencies and run this script again"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Python Dependencies"
    
    if [ -f "pyproject.toml" ]; then
        print_info "Installing project dependencies with UV..."
        uv sync
        print_success "Dependencies installed successfully"
        
        print_info "Installing development dependencies..."
        uv sync --dev
        print_success "Development dependencies installed successfully"
    else
        print_error "pyproject.toml not found. Are you in the project root directory?"
        exit 1
    fi
}

# Setup development environment
setup_dev_environment() {
    print_header "Setting Up Development Environment"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info "Creating .env file with default configuration..."
        cat > .env << EOF
# FastAPI Jaeger Tracing Configuration
SERVICE_NAME=fastapi-jaeger-demo
JAEGER_HOST=localhost
JAEGER_PORT=14268
ENVIRONMENT=development

# Optional: Database configuration
DATABASE_URL=sqlite:///./demo.db

# Optional: Redis configuration  
REDIS_URL=redis://localhost:6379

# Development settings
DEBUG=true
LOG_LEVEL=INFO
EOF
        print_success ".env file created"
    else
        print_info ".env file already exists, skipping..."
    fi
    
    # Create logs directory
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_success "Logs directory created"
    fi
    
    # Create data directory for development
    if [ ! -d "data" ]; then
        mkdir -p data
        print_success "Data directory created"
    fi
}

# Test installation
test_installation() {
    print_header "Testing Installation"
    
    # Test Python imports
    print_info "Testing Python dependencies..."
    uv run python -c "from opentelemetry import trace; from fastapi import FastAPI; print('Core dependencies working')" || {
        print_error "Python dependency test failed"
        exit 1
    }
    
    # Test application startup (quick test)
    print_info "Testing application startup..."
    timeout 10s uv run python -c "
from app.main import app
from config import setup_tracing
print('Application imports working')
" || {
        print_error "Application startup test failed"
        exit 1
    }
    
    print_success "Installation tests passed"
}

# Start Jaeger (if Docker is available)
start_jaeger() {
    if command_exists docker; then
        print_header "Starting Jaeger"
        
        print_info "Starting Jaeger with Docker Compose..."
        if [ -f "docker-compose.dev.yml" ]; then
            docker-compose -f docker-compose.dev.yml up -d jaeger
            
            # Wait for Jaeger to be ready
            print_info "Waiting for Jaeger to be ready..."
            for i in {1..30}; do
                if curl -f http://localhost:16686/ >/dev/null 2>&1; then
                    print_success "Jaeger is ready!"
                    break
                fi
                echo -n "."
                sleep 2
            done
            echo ""
            
            print_success "Jaeger UI available at: http://localhost:16686"
        else
            print_error "docker-compose.dev.yml not found"
        fi
    else
        print_warning "Docker not available, skipping Jaeger startup"
        print_info "You can install Jaeger manually or use Docker later"
    fi
}

# Print final instructions
print_instructions() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}FastAPI Jaeger Tracing Demo is ready!${NC}"
    echo ""
    echo "Quick Start Commands:"
    echo "===================="
    echo ""
    echo "1. Start the application in development mode:"
    echo "   ${YELLOW}make run-dev${NC}"
    echo "   or"
    echo "   ${YELLOW}uv run uvicorn app.main:app --reload${NC}"
    echo ""
    echo "2. Generate sample traffic:"
    echo "   ${YELLOW}make traffic${NC}"
    echo "   or"
    echo "   ${YELLOW}uv run python scripts/generate_traffic.py${NC}"
    echo ""
    echo "3. Run load tests:"
    echo "   ${YELLOW}make load-test${NC}"
    echo ""
    echo "4. Start full Docker environment:"
    echo "   ${YELLOW}make docker-up${NC}"
    echo ""
    echo "5. Run complete demo:"
    echo "   ${YELLOW}make demo${NC}"
    echo ""
    echo "Important URLs:"
    echo "=============="
    echo "• Application:    ${BLUE}http://localhost:8000${NC}"
    echo "• API Docs:       ${BLUE}http://localhost:8000/docs${NC}"
    echo "• Health Check:   ${BLUE}http://localhost:8000/health${NC}"
    echo "• Jaeger UI:      ${BLUE}http://localhost:16686${NC}"
    echo ""
    echo "Useful Commands:"
    echo "==============="
    echo "• ${YELLOW}make help${NC}          - Show all available commands"
    echo "• ${YELLOW}make health${NC}        - Check service health"
    echo "• ${YELLOW}make status${NC}        - Show service status"
    echo "• ${YELLOW}make logs-app${NC}      - View application logs"
    echo "• ${YELLOW}make clean${NC}         - Clean up temporary files"
    echo ""
    echo "Development Workflow:"
    echo "===================="
    echo "1. Start Jaeger: ${YELLOW}make run-jaeger${NC}"
    echo "2. Start app: ${YELLOW}make run-dev${NC}"
    echo "3. Generate traffic: ${YELLOW}make traffic${NC}"
    echo "4. View traces in Jaeger UI"
    echo ""
    print_success "Happy tracing!"
}

# Main execution
main() {
    print_header "FastAPI Jaeger Tracing Demo Setup"
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_info "Starting setup process..."
    
    check_prerequisites
    install_dependencies
    setup_dev_environment
    test_installation
    start_jaeger
    print_instructions
}

# Parse command line arguments
case "${1:-setup}" in
    "setup"|"")
        main
        ;;
    "check")
        check_prerequisites
        ;;
    "install")
        install_dependencies
        ;;
    "test")
        test_installation
        ;;
    "jaeger")
        start_jaeger
        ;;
    "help"|"-h"|"--help")
        echo "FastAPI Jaeger Tracing Demo Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup    - Full setup (default)"
        echo "  check    - Check prerequisites only"
        echo "  install  - Install dependencies only"
        echo "  test     - Test installation only"
        echo "  jaeger   - Start Jaeger only"
        echo "  help     - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac