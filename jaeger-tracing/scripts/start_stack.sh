#!/bin/bash

# Start the complete observability stack
# This script starts all services in the correct order

set -e

echo "Starting FastAPI + Jaeger + Kibana + Elasticsearch Stack"
echo "========================================================"
echo ""

# Use the full stack startup script
./scripts/start_full_stack.sh

# Start FastAPI application
echo "Starting FastAPI application..."
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

# Wait for FastAPI to be ready
echo "Waiting for FastAPI to be ready..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "[SUCCESS] FastAPI is ready!"
        break
    fi
    echo -n "."
    sleep 2
    counter=$((counter + 2))
done
echo ""

if [ $counter -ge $timeout ]; then
    echo "[ERROR] FastAPI failed to start within $timeout seconds"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "[SUCCESS] Complete stack is ready!"
echo ""
echo "Services:"
echo "  - FastAPI Application: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Jaeger UI: http://localhost:16686"
echo "  - Kibana: http://localhost:5601"
echo "  - Elasticsearch: http://localhost:9200"
echo ""
echo "To stop the stack:"
echo "  - Press Ctrl+C to stop FastAPI"
echo "  - Run: docker-compose down"
echo ""
echo "FastAPI PID: $APP_PID"
echo "Keeping FastAPI running in background..."

# Keep the script running to maintain the FastAPI process
wait $APP_PID