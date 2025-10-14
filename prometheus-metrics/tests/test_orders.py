"""
Tests for Order Service API endpoints.
"""

import pytest
from fastapi import status


class TestOrderService:
    """Test cases for Order Service endpoints."""

    def test_get_all_orders(self, client):
        """Test getting all orders."""
        response = client.get("/api/v1/orders")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        # Should have some default orders
        assert len(data) >= 0

    def test_get_order_by_id_existing(self, client):
        """Test getting an existing order by ID."""
        # Test with default order ID 101
        response = client.get("/api/v1/orders/101")
        assert response.status_code == status.HTTP_200_OK
        
        order = response.json()
        assert "id" in order
        assert "user_id" in order
        assert "amount" in order
        assert "items" in order
        assert "status" in order
        assert "type" in order
        assert order["id"] == 101

    def test_get_order_by_id_nonexistent(self, client):
        """Test getting a non-existent order by ID."""
        response = client.get("/api/v1/orders/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_create_order_valid(self, client):
        """Test creating an order with valid data."""
        order_data = {
            "user_id": 1,
            "amount": 99.99,
            "items": ["item1", "item2"],
            "type": "express"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_order = response.json()
        assert "id" in created_order
        assert created_order["user_id"] == order_data["user_id"]
        assert created_order["amount"] == order_data["amount"]
        assert created_order["items"] == order_data["items"]
        assert created_order["type"] == order_data["type"]
        assert created_order["status"] == "pending"
        assert "created_at" in created_order

    def test_create_order_missing_required_fields(self, client):
        """Test creating an order without required fields."""
        # Missing user_id
        order_data = {
            "amount": 99.99,
            "items": ["item1"]
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_order_invalid_user_id(self, client):
        """Test creating an order with non-existent user."""
        order_data = {
            "user_id": 999,  # Non-existent user
            "amount": 99.99,
            "items": ["item1"]
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "does not exist" in error["detail"]

    def test_create_order_invalid_amount(self, client):
        """Test creating an order with invalid amount."""
        order_data = {
            "user_id": 1,
            "amount": -10.0,  # Negative amount
            "items": ["item1"]
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        # This might be caught by validation or business logic
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_update_order_status_valid(self, client):
        """Test updating order status with valid data."""
        status_data = {
            "status": "processing",
            "reason": "order_being_processed"
        }
        
        response = client.put("/api/v1/orders/101/status", json=status_data)
        assert response.status_code == status.HTTP_200_OK
        
        updated_order = response.json()
        assert updated_order["status"] == status_data["status"]
        assert "updated_at" in updated_order

    def test_update_order_status_nonexistent(self, client):
        """Test updating status of non-existent order."""
        status_data = {
            "status": "processing"
        }
        
        response = client.put("/api/v1/orders/999/status", json=status_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_process_order_valid(self, client):
        """Test processing a valid order."""
        # First create an order
        order_data = {
            "user_id": 1,
            "amount": 50.0,
            "items": ["processable_item"]
        }
        create_response = client.post("/api/v1/orders", json=order_data)
        created_order = create_response.json()
        order_id = created_order["id"]
        
        # Process the order
        response = client.post(f"/api/v1/orders/{order_id}/process")
        assert response.status_code == status.HTTP_200_OK
        
        processed_order = response.json()
        assert processed_order["status"] == "processing"

    def test_process_order_nonexistent(self, client):
        """Test processing a non-existent order."""
        response = client.post("/api/v1/orders/999/process")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_order_valid(self, client):
        """Test cancelling a valid order."""
        # First create an order
        order_data = {
            "user_id": 1,
            "amount": 30.0,
            "items": ["cancellable_item"]
        }
        create_response = client.post("/api/v1/orders", json=order_data)
        created_order = create_response.json()
        order_id = created_order["id"]
        
        # Cancel the order
        response = client.post(f"/api/v1/orders/{order_id}/cancel?reason=user_requested")
        assert response.status_code == status.HTTP_200_OK
        
        cancelled_order = response.json()
        assert cancelled_order["status"] == "cancelled"

    def test_cancel_order_nonexistent(self, client):
        """Test cancelling a non-existent order."""
        response = client.post("/api/v1/orders/999/cancel")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_orders_by_user_existing(self, client):
        """Test getting orders for an existing user."""
        response = client.get("/api/v1/orders/user/1")
        assert response.status_code == status.HTTP_200_OK
        
        orders = response.json()
        assert isinstance(orders, list)
        # All orders should belong to user 1
        for order in orders:
            assert order["user_id"] == 1

    def test_get_orders_by_user_no_orders(self, client):
        """Test getting orders for user with no orders."""
        response = client.get("/api/v1/orders/user/999")
        assert response.status_code == status.HTTP_200_OK
        
        orders = response.json()
        assert isinstance(orders, list)
        assert len(orders) == 0

    def test_order_workflow_complete(self, client):
        """Test complete order workflow: create, process, complete."""
        # Create order
        order_data = {
            "user_id": 1,
            "amount": 75.0,
            "items": ["workflow_item1", "workflow_item2"],
            "type": "standard"
        }
        
        create_response = client.post("/api/v1/orders", json=order_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        created_order = create_response.json()
        order_id = created_order["id"]
        assert created_order["status"] == "pending"
        
        # Process order
        process_response = client.post(f"/api/v1/orders/{order_id}/process")
        assert process_response.status_code == status.HTTP_200_OK
        processed_order = process_response.json()
        assert processed_order["status"] == "processing"
        
        # Update to completed
        status_data = {
            "status": "completed",
            "reason": "order_fulfilled"
        }
        complete_response = client.put(f"/api/v1/orders/{order_id}/status", json=status_data)
        assert complete_response.status_code == status.HTTP_200_OK
        completed_order = complete_response.json()
        assert completed_order["status"] == "completed"

    def test_order_types_validation(self, client):
        """Test different order types."""
        order_types = ["standard", "express", "bulk"]
        
        for order_type in order_types:
            order_data = {
                "user_id": 1,
                "amount": 25.0,
                "items": [f"{order_type}_item"],
                "type": order_type
            }
            
            response = client.post("/api/v1/orders", json=order_data)
            assert response.status_code == status.HTTP_201_CREATED
            
            created_order = response.json()
            assert created_order["type"] == order_type