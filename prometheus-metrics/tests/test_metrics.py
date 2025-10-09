"""
Test metrics endpoint and collection.
"""

def test_metrics_endpoint_exists(client):
    """Test that metrics endpoint exists."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_content(client):
    """Test that metrics contain expected data."""
    # Make some requests to generate metrics
    client.get("/health/")
    client.get("/api/v1/users")
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Check for HTTP metrics
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "http_requests_active" in content


def test_custom_metrics_after_api_calls(client):
    """Test that custom metrics are generated after API calls."""
    # Make API call
    client.get("/api/v1/users")
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should contain custom business metrics
    assert "user_operations_total" in content