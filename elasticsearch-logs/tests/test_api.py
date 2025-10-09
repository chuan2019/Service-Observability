"""Test cases for API endpoints."""


from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint(self, client: TestClient):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_detailed_health_endpoint(self, client: TestClient):
        """Test detailed health endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "uptime" in data


class TestUserEndpoints:
    """Test user management endpoints."""

    def test_get_users(self, client: TestClient):
        """Test getting list of users."""
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check first user structure
        user = data[0]
        assert "id" in user
        assert "name" in user
        assert "email" in user
        assert "is_active" in user

    def test_get_users_with_pagination(self, client: TestClient):
        """Test user pagination."""
        response = client.get("/api/v1/users?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_users_active_only(self, client: TestClient):
        """Test filtering active users only."""
        response = client.get("/api/v1/users?active_only=true")
        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["is_active"] is True

    def test_get_user_by_id(self, client: TestClient):
        """Test getting user by ID."""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "email" in data

    def test_get_nonexistent_user(self, client: TestClient):
        """Test getting non-existent user returns 404."""
        response = client.get("/api/v1/users/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_create_user(self, client: TestClient, sample_user_data):
        """Test creating a new user."""
        response = client.post("/api/v1/users", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data

    def test_create_user_duplicate_email(self, client: TestClient):
        """Test creating user with duplicate email fails."""
        user_data = {"name": "Test User", "email": "john@example.com"}  # Existing email
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]

    def test_create_user_invalid_email(self, client: TestClient):
        """Test creating user with invalid email fails."""
        user_data = {"name": "Test User", "email": "invalid-email"}
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_update_user(self, client: TestClient):
        """Test updating an existing user."""
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/users/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == 1

    def test_update_nonexistent_user(self, client: TestClient):
        """Test updating non-existent user returns 404."""
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/users/999", json=update_data)
        assert response.status_code == 404

    def test_delete_user(self, client: TestClient):
        """Test deleting a user."""
        response = client.delete("/api/v1/users/2")
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_delete_nonexistent_user(self, client: TestClient):
        """Test deleting non-existent user returns 404."""
        response = client.delete("/api/v1/users/999")
        assert response.status_code == 404


class TestOrderEndpoints:
    """Test order management endpoints."""

    def test_get_orders(self, client: TestClient):
        """Test getting list of orders."""
        response = client.get("/api/v1/orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check first order structure
        order = data[0]
        assert "id" in order
        assert "user_id" in order
        assert "product_name" in order
        assert "quantity" in order
        assert "price" in order
        assert "status" in order

    def test_get_orders_with_filters(self, client: TestClient):
        """Test order filtering."""
        response = client.get("/api/v1/orders?status=pending")
        assert response.status_code == 200
        data = response.json()
        for order in data:
            assert order["status"] == "pending"

    def test_get_orders_by_user(self, client: TestClient):
        """Test filtering orders by user ID."""
        response = client.get("/api/v1/orders?user_id=1")
        assert response.status_code == 200
        data = response.json()
        for order in data:
            assert order["user_id"] == 1

    def test_get_order_by_id(self, client: TestClient):
        """Test getting order by ID."""
        response = client.get("/api/v1/orders/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "product_name" in data

    def test_get_nonexistent_order(self, client: TestClient):
        """Test getting non-existent order returns 404."""
        response = client.get("/api/v1/orders/999")
        assert response.status_code == 404

    def test_create_order(self, client: TestClient, sample_order_data):
        """Test creating a new order."""
        response = client.post("/api/v1/orders", json=sample_order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == sample_order_data["user_id"]
        assert data["product_name"] == sample_order_data["product_name"]
        assert data["quantity"] == sample_order_data["quantity"]
        assert data["price"] == sample_order_data["price"]
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_order_invalid_data(self, client: TestClient):
        """Test creating order with invalid data fails."""
        invalid_data = {
            "user_id": 1,
            "product_name": "Test",
            "quantity": 0,
            "price": -10,
        }
        response = client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_update_order_status(self, client: TestClient):
        """Test updating order status."""
        update_data = {"status": "processing"}
        response = client.put("/api/v1/orders/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

    def test_cancel_order(self, client: TestClient):
        """Test cancelling an order."""
        response = client.delete("/api/v1/orders/2")
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["message"]

    def test_cancel_shipped_order_fails(self, client: TestClient):
        """Test that cancelling shipped order fails."""
        # First update order to shipped
        client.put("/api/v1/orders/3", json={"status": "shipped"})

        # Then try to cancel
        response = client.delete("/api/v1/orders/3")
        assert response.status_code == 400
        data = response.json()
        assert "Cannot cancel order" in data["detail"]


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
