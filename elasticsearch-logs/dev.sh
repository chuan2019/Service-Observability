#!/bin/bash

# FastAPI Elasticsearch Logs - Development Environment Manager

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_usage() {
    echo -e "${BLUE}FastAPI Elasticsearch Logs - Development Environment Manager${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start        Start the development environment (Elasticsearch + Kibana + FastAPI)"
    echo "  stop         Stop all services"
    echo "  restart      Restart all services"
    echo "  logs         Show logs for all services"
    echo "  logs-app     Show logs for FastAPI app only"
    echo "  logs-es      Show logs for Elasticsearch only"
    echo "  logs-kibana  Show logs for Kibana only"
    echo "  build        Build the development Docker image"
    echo "  shell        Open a shell in the FastAPI container"
    echo "  test         Run tests in the container"
    echo "  status       Show status of all services"
    echo "  clean        Stop and remove all containers, networks, and volumes"
    echo "  help         Show this help message"
    echo ""
    echo "URLs:"
    echo "  FastAPI App:    http://localhost:8000"
    echo "  Elasticsearch:  http://localhost:9200"
    echo "  Kibana:         http://localhost:5601"
}

start_dev() {
    echo -e "${GREEN}Starting development environment...${NC}"
    docker-compose --profile dev up -d
    echo -e "${GREEN}Development environment started!${NC}"
    echo ""
    echo -e "${YELLOW}Services:${NC}"
    echo "  FastAPI App:    http://localhost:8000"
    echo "  FastAPI Docs:   http://localhost:8000/docs"
    echo "  Elasticsearch:  http://localhost:9200"
    echo "  Kibana:         http://localhost:5601"
    echo ""
    echo -e "${YELLOW}Use '$0 logs' to view logs${NC}"
}

stop_dev() {
    echo -e "${YELLOW}Stopping development environment...${NC}"
    docker-compose --profile dev down
    echo -e "${GREEN}Development environment stopped!${NC}"
}

restart_dev() {
    echo -e "${YELLOW}Restarting development environment...${NC}"
    docker-compose --profile dev restart
    echo -e "${GREEN}Development environment restarted!${NC}"
}

show_logs() {
    docker-compose --profile dev logs -f
}

show_app_logs() {
    docker-compose --profile dev logs -f fastapi-dev
}

show_es_logs() {
    docker-compose --profile dev logs -f elasticsearch
}

show_kibana_logs() {
    docker-compose --profile dev logs -f kibana
}

build_dev() {
    echo -e "${GREEN}Building development Docker image...${NC}"
    docker-compose build fastapi-dev
    echo -e "${GREEN}Build completed!${NC}"
}

shell_access() {
    echo -e "${GREEN}Opening shell in FastAPI container...${NC}"
    docker-compose --profile dev exec fastapi-dev bash
}

run_tests() {
    echo -e "${GREEN}Running tests in container...${NC}"
    docker-compose --profile dev exec fastapi-dev uv run python -m pytest tests/ -v
}

show_status() {
    echo -e "${BLUE}Development Environment Status:${NC}"
    docker-compose --profile dev ps
}

clean_all() {
    echo -e "${RED}Cleaning up all containers, networks, and volumes...${NC}"
    read -p "Are you sure? This will remove all data. (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile dev down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}Cleanup completed!${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled.${NC}"
    fi
}

# Main script logic
case "$1" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev
        ;;
    logs)
        show_logs
        ;;
    logs-app)
        show_app_logs
        ;;
    logs-es)
        show_es_logs
        ;;
    logs-kibana)
        show_kibana_logs
        ;;
    build)
        build_dev
        ;;
    shell)
        shell_access
        ;;
    test)
        run_tests
        ;;
    status)
        show_status
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac