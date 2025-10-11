#!/bin/bash
# Demo script to show Docker development with hot reload

echo "=== FastAPI Docker Development Demo ==="
echo "Current response from container:"
curl -s http://localhost:8000/ | jq -r '.message'

echo ""
echo "Modifying source code..."
# Modify the message in main.py
sed -i 's/HOT RELOAD TEST!/HOT RELOAD WORKING PERFECTLY!/' /home/chuan/Documents/My_Study/Python/fastapi/Service-Observability/jaeger-tracing/app/main.py

echo "Waiting 5 seconds for hot reload..."
sleep 5

echo ""
echo "New response from container:"
curl -s http://localhost:8000/ | jq -r '.message'

echo ""
echo "Hot reload demonstration complete!"
echo "Services are running in Docker containers with local code mounted for development."