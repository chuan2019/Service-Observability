#!/bin/bash

# E-Commerce Microservices Startup Script

echo "E-Commerce Microservices with Prometheus & Grafana"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: No virtual environment detected"
    echo "Consider activating a virtual environment first:"
    echo "python -m venv venv && source venv/bin/activate"
    echo ""
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database and sample data
echo "Initializing database and sample data..."
python scripts/init_sample_data.py

# Start services
echo "Starting services..."
echo ""
echo "Starting FastAPI application with Prometheus metrics..."
echo "Application will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo "Metrics endpoint at: http://localhost:8000/metrics"
echo ""
echo "To start with Docker Compose (Prometheus + Grafana):"
echo "docker-compose up -d"
echo ""
echo "Grafana will be at: http://localhost:3000 (admin/admin)"
echo "Prometheus will be at: http://localhost:9090"
echo ""

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000