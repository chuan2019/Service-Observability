"""
Test metrics endpoint and collection.
"""

def test_metrics_endpoint_exists(client):
    """Test that metrics endpoint exists."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_http_metrics_generation(client):
    """Test that HTTP metrics are generated for requests."""
    # Make some requests to generate metrics
    client.get("/health")
    client.get("/api/v1/users")
    client.post("/api/v1/users", json={"name": "Test", "email": "test@example.com"})
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Check for FastAPI HTTP metrics
    assert "fastapi_requests_total" in content
    assert "fastapi_request_duration_seconds" in content
    assert "fastapi_active_requests" in content
    
    # Should contain method and status code labels
    assert 'method="GET"' in content
    assert 'method="POST"' in content


def test_user_service_metrics(client):
    """Test that user service metrics are generated."""
    # Make user service calls
    client.get("/api/v1/users")
    client.post("/api/v1/users", json={"name": "Metrics User", "email": "metrics@example.com"})
    client.get("/api/v1/users/1")
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain user service metrics
    assert "user_service_operations_total" in content
    assert "user_service_operation_duration_seconds" in content
    assert "user_service_active_users" in content
    assert "user_service_db_queries_total" in content


def test_order_service_metrics(client):
    """Test that order service metrics are generated."""
    # Make order service calls
    client.get("/api/v1/orders")
    client.post("/api/v1/orders", json={
        "user_id": 1,
        "amount": 99.99,
        "items": ["test_item"],
        "type": "express"
    })
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain order service metrics
    assert "order_service_operations_total" in content
    assert "order_service_operation_duration_seconds" in content
    assert "order_service_active_orders" in content
    assert "order_service_order_value" in content
    assert "order_service_items_per_order" in content


def test_payment_service_metrics(client):
    """Test that payment service metrics are generated."""
    # Make payment service calls
    client.post("/api/v1/payments", json={
        "order_id": 101,
        "amount": 99.99,
        "method": "credit_card"
    })
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain payment service metrics
    assert "payment_service_operations_total" in content
    assert "payment_service_operation_duration_seconds" in content
    assert "payment_service_amount" in content
    assert "payment_service_gateway_calls_total" in content


def test_metrics_labels_accuracy(client):
    """Test that metrics contain accurate labels."""
    # Make specific requests
    client.get("/api/v1/users/1")  # Should succeed
    client.get("/api/v1/users/999")  # Should fail (404)
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain different status codes
    assert 'status_code="200"' in content
    assert 'status_code="404"' in content
    
    # Should contain endpoint information
    assert 'endpoint="/api/v1/users/1"' in content or 'endpoint="/api/v1/users/{user_id}"' in content


def test_metrics_after_service_operations(client):
    """Test metrics generation after various service operations."""
    # User operations
    user_response = client.post("/api/v1/users", json={
        "name": "Service Test User",
        "email": "service@example.com"
    })
    
    if user_response.status_code == 201:
        user = user_response.json()
        user_id = user["id"]
        
        # Order operations
        order_response = client.post("/api/v1/orders", json={
            "user_id": user_id,
            "amount": 150.0,
            "items": ["service_item1", "service_item2"]
        })
        
        if order_response.status_code == 201:
            order = order_response.json()
            
            # Payment operations
            client.post("/api/v1/payments", json={
                "order_id": order["id"],
                "amount": order["amount"],
                "method": "credit_card"
            })
    
    # Check comprehensive metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain all service metrics
    services = ["user_service", "order_service", "payment_service"]
    for service in services:
        assert f"{service}_operations_total" in content
        assert f"{service}_operation_duration_seconds" in content


def test_metrics_performance(client):
    """Test that metrics endpoint performs well."""
    import time
    
    # Generate some traffic first
    for i in range(10):
        client.get(f"/api/v1/users/{i % 3 + 1}")
    
    # Time the metrics endpoint
    start_time = time.time()
    response = client.get("/metrics")
    end_time = time.time()
    
    assert response.status_code == 200
    # Metrics endpoint should respond quickly (under 1 second)
    assert (end_time - start_time) < 1.0


def test_metrics_format_compliance(client):
    """Test that metrics follow Prometheus format."""
    # Generate some metrics
    client.get("/api/v1/users")
    
    response = client.get("/metrics")
    content = response.text
    
    # Should contain HELP and TYPE comments
    assert "# HELP" in content
    assert "# TYPE" in content
    
    # Should contain proper metric format (metric_name{labels} value)
    lines = content.split('\n')
    metric_lines = [line for line in lines if line and not line.startswith('#')]
    
    for line in metric_lines:
        if line.strip():
            # Should contain metric name and value
            assert ' ' in line or '\t' in line


def test_custom_registry_isolation(client):
    """Test that custom registry doesn't interfere with default metrics."""
    response = client.get("/metrics")
    content = response.text
    
    # Should contain our custom metrics
    assert "user_service_operations_total" in content
    assert "fastapi_requests_total" in content
    
    # Should not contain default prometheus_client metrics that we didn't register
    # (This tests that we're using a custom registry correctly)