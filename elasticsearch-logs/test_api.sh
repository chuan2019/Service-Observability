#!/bin/bash
echo "Starting FastAPI application..."
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 &
APP_PID=$!
sleep 5

echo "Testing health endpoint..."
curl -s http://127.0.0.1:8001/health

echo -e "\nTesting users endpoint..."
curl -s http://127.0.0.1:8001/api/v1/users

echo -e "\nTesting root endpoint..."
curl -s http://127.0.0.1:8001/

echo -e "\nStopping application..."
kill $APP_PID
wait $APP_PID 2>/dev/null || true
echo "Test completed!"
