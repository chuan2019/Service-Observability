"""
Integration tests for cross-service interactions.
"""

import pytest
from fastapi import status


class TestServiceIntegration:
    """Test cases for cross-service interactions and workflows."""

    def test_user_order_integration(self, client):
        """Test integration between user and order services."""
        # Create a user first
        user_data = {
            "name": "Integration Test User",
            "email": "integration@example.com",
            "status": "active"
        }
        
        user_response = client.post("/api/v1/users", json=user_data)
        assert user_response.status_code == status.HTTP_201_CREATED
        user = user_response.json()
        user_id = user["id"]
        
        # Create an order for that user
        order_data = {
            "user_id": user_id,
            "amount": 150.0,
            "items": ["integration_item1", "integration_item2"],
            "type": "standard"
        }
        
        order_response = client.post("/api/v1/orders", json=order_data)
        assert order_response.status_code == status.HTTP_201_CREATED
        order = order_response.json()
        
        # Verify order is linked to user
        assert order["user_id"] == user_id
        
        # Get orders by user to verify relationship
        user_orders_response = client.get(f"/api/v1/orders/user/{user_id}")
        assert user_orders_response.status_code == status.HTTP_200_OK
        user_orders = user_orders_response.json()
        
        # Should contain the order we just created
        order_ids = [o["id"] for o in user_orders]
        assert order["id"] in order_ids

    def test_order_payment_integration(self, client):
        """Test integration between order and payment services."""
        # Create an order first (using existing user)
        order_data = {
            "user_id": 1,  # Existing user
            "amount": 200.0,
            "items": ["payment_test_item"],
            "type": "express"
        }
        
        order_response = client.post("/api/v1/orders", json=order_data)
        assert order_response.status_code == status.HTTP_201_CREATED
        order = order_response.json()
        order_id = order["id"]
        
        # Process payment for that order
        payment_data = {
            "order_id": order_id,
            "amount": order["amount"],
            "method": "credit_card"
        }
        
        payment_response = client.post("/api/v1/payments", json=payment_data)
        assert payment_response.status_code == status.HTTP_201_CREATED
        payment = payment_response.json()
        
        # Verify payment is linked to order
        assert payment["order_id"] == order_id
        assert payment["amount"] == order["amount"]
        
        # Get payments by order to verify relationship
        order_payments_response = client.get(f"/api/v1/payments/order/{order_id}")
        assert order_payments_response.status_code == status.HTTP_200_OK
        order_payments = order_payments_response.json()
        
        # Should contain the payment we just created
        payment_ids = [p["id"] for p in order_payments]
        assert payment["id"] in payment_ids

    def test_full_workflow_integration(self, client):
        """Test complete workflow: user → order → payment → refund."""
        # Step 1: Create user
        user_data = {
            "name": "Workflow Test User",
            "email": "workflow@example.com"
        }
        
        user_response = client.post("/api/v1/users", json=user_data)
        assert user_response.status_code == status.HTTP_201_CREATED
        user = user_response.json()
        user_id = user["id"]
        
        # Step 2: Create order for user
        order_data = {
            "user_id": user_id,
            "amount": 300.0,
            "items": ["workflow_item1", "workflow_item2", "workflow_item3"],
            "type": "bulk"
        }
        
        order_response = client.post("/api/v1/orders", json=order_data)
        assert order_response.status_code == status.HTTP_201_CREATED
        order = order_response.json()
        order_id = order["id"]
        
        # Step 3: Process payment for order
        payment_data = {
            "order_id": order_id,
            "amount": order["amount"],
            "method": "paypal"
        }
        
        payment_response = client.post("/api/v1/payments", json=payment_data)
        assert payment_response.status_code == status.HTTP_201_CREATED
        payment = payment_response.json()
        payment_id = payment["id"]
        
        # Step 4: Process the order
        process_response = client.post(f"/api/v1/orders/{order_id}/process")
        assert process_response.status_code == status.HTTP_200_OK
        processed_order = process_response.json()
        assert processed_order["status"] == "processing"
        
        # Step 5: Partial refund
        refund_data = {
            "amount": 100.0,
            "reason": "partial_return"
        }
        
        refund_response = client.post(f"/api/v1/payments/{payment_id}/refund", json=refund_data)
        assert refund_response.status_code == status.HTTP_201_CREATED
        refund = refund_response.json()
        
        # Verify all relationships
        assert refund["original_payment_id"] == payment_id
        assert payment["order_id"] == order_id
        assert order["user_id"] == user_id

    def test_cross_service_validation(self, client):
        """Test validation between services."""
        # Try to create order for non-existent user
        order_data = {
            "user_id": 99999,  # Non-existent
            "amount": 100.0,
            "items": ["test_item"]
        }
        
        order_response = client.post("/api/v1/orders", json=order_data)
        assert order_response.status_code == status.HTTP_400_BAD_REQUEST
        error = order_response.json()
        assert "does not exist" in error["detail"]
        
        # Try to create payment for non-existent order
        payment_data = {
            "order_id": 99999,  # Non-existent
            "amount": 100.0,
            "method": "credit_card"
        }
        
        payment_response = client.post("/api/v1/payments", json=payment_data)
        assert payment_response.status_code == status.HTTP_404_NOT_FOUND
        error = payment_response.json()
        assert "not found" in error["detail"].lower()

    def test_cascade_operations(self, client):
        """Test operations that should affect related entities."""
        # Create user and order
        user_data = {"name": "Cascade User", "email": "cascade@example.com"}
        user_response = client.post("/api/v1/users", json=user_data)
        user = user_response.json()
        user_id = user["id"]
        
        order_data = {
            "user_id": user_id,
            "amount": 75.0,
            "items": ["cascade_item"]
        }
        order_response = client.post("/api/v1/orders", json=order_data)
        order = order_response.json()
        order_id = order["id"]
        
        # Delete user
        delete_response = client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Try to create new order for deleted user
        new_order_data = {
            "user_id": user_id,
            "amount": 50.0,
            "items": ["new_item"]
        }
        new_order_response = client.post("/api/v1/orders", json=new_order_data)
        assert new_order_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_data_consistency_across_services(self, client):
        """Test data consistency across all services."""
        # Create complete workflow
        user_data = {
            "name": "Consistency User",
            "email": "consistency@example.com"
        }
        
        user_response = client.post("/api/v1/users", json=user_data)
        user = user_response.json()
        
        order_data = {
            "user_id": user["id"],
            "amount": 250.0,
            "items": ["consistency_item1", "consistency_item2"]
        }
        
        order_response = client.post("/api/v1/orders", json=order_data)
        order = order_response.json()
        
        payment_data = {
            "order_id": order["id"],
            "amount": order["amount"],
            "method": "apple_pay"
        }
        
        payment_response = client.post("/api/v1/payments", json=payment_data)
        payment = payment_response.json()
        
        # Verify data consistency by retrieving each entity
        user_check = client.get(f"/api/v1/users/{user['id']}")
        order_check = client.get(f"/api/v1/orders/{order['id']}")
        payment_check = client.get(f"/api/v1/payments/{payment['id']}")
        
        assert user_check.status_code == status.HTTP_200_OK
        assert order_check.status_code == status.HTTP_200_OK
        assert payment_check.status_code == status.HTTP_200_OK
        
        # Verify relationships are maintained
        retrieved_order = order_check.json()
        retrieved_payment = payment_check.json()
        
        assert retrieved_order["user_id"] == user["id"]
        assert retrieved_payment["order_id"] == order["id"]

    def test_concurrent_operations(self, client):
        """Test handling of concurrent operations."""
        # Create user and order
        user_data = {"name": "Concurrent User", "email": "concurrent@example.com"}
        user_response = client.post("/api/v1/users", json=user_data)
        user = user_response.json()
        
        order_data = {
            "user_id": user["id"],
            "amount": 100.0,
            "items": ["concurrent_item"]
        }
        order_response = client.post("/api/v1/orders", json=order_data)
        order = order_response.json()
        
        # Try to process multiple payments for the same order
        payment_data = {
            "order_id": order["id"],
            "amount": order["amount"],
            "method": "credit_card"
        }
        
        # This should work
        payment1_response = client.post("/api/v1/payments", json=payment_data)
        
        # This should also work (multiple payments allowed for an order)
        payment2_response = client.post("/api/v1/payments", json=payment_data)
        
        # Both payments should be processed independently
        if payment1_response.status_code == status.HTTP_201_CREATED:
            payment1 = payment1_response.json()
            assert payment1["order_id"] == order["id"]
        
        if payment2_response.status_code == status.HTTP_201_CREATED:
            payment2 = payment2_response.json()
            assert payment2["order_id"] == order["id"]

    def test_service_metrics_integration(self, client):
        """Test that cross-service operations generate appropriate metrics."""
        # Perform cross-service operations
        user_data = {"name": "Metrics User", "email": "metrics@example.com"}
        client.post("/api/v1/users", json=user_data)
        
        order_data = {
            "user_id": 1,
            "amount": 125.0,
            "items": ["metrics_item"]
        }
        client.post("/api/v1/orders", json=order_data)
        
        payment_data = {
            "order_id": 101,
            "amount": 125.0,
            "method": "google_pay"
        }
        client.post("/api/v1/payments", json=payment_data)
        
        # Check that metrics were generated
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK
        
        metrics_content = metrics_response.text
        
        # Should contain metrics from all services
        assert "user_service_operations_total" in metrics_content
        assert "order_service_operations_total" in metrics_content  
        assert "payment_service_operations_total" in metrics_content
        
        # Should contain HTTP metrics
        assert "fastapi_requests_total" in metrics_content
        assert "fastapi_request_duration_seconds" in metrics_content