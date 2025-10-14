"""
Tests for Payment Service API endpoints.
"""

import pytest
from fastapi import status


class TestPaymentService:
    """Test cases for Payment Service endpoints."""

    def test_process_payment_valid(self, client):
        """Test processing a payment with valid data."""
        payment_data = {
            "order_id": 101,  # Default order
            "amount": 99.99,
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        payment = response.json()
        assert "id" in payment
        assert payment["order_id"] == payment_data["order_id"]
        assert payment["amount"] == payment_data["amount"]
        assert payment["method"] == payment_data["method"]
        assert payment["status"] == "completed"
        assert "gateway_transaction_id" in payment
        assert "processing_fee" in payment
        assert "net_amount" in payment
        assert "created_at" in payment
        assert "processed_at" in payment

    def test_process_payment_missing_fields(self, client):
        """Test processing payment with missing required fields."""
        # Missing order_id
        payment_data = {
            "amount": 99.99,
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_process_payment_invalid_order(self, client):
        """Test processing payment for non-existent order."""
        payment_data = {
            "order_id": 999,  # Non-existent order
            "amount": 99.99,
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error = response.json()
        assert "not found" in error["detail"].lower()

    def test_process_payment_invalid_amount(self, client):
        """Test processing payment with invalid amount."""
        payment_data = {
            "order_id": 101,
            "amount": -50.0,  # Negative amount
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "greater than 0" in error["detail"]

    def test_process_payment_zero_amount(self, client):
        """Test processing payment with zero amount."""
        payment_data = {
            "order_id": 101,
            "amount": 0.0,
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_process_payment_excessive_amount(self, client):
        """Test processing payment with amount exceeding limit."""
        payment_data = {
            "order_id": 101,
            "amount": 15000.0,  # Above 10000 limit
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "exceeds maximum limit" in error["detail"]

    def test_process_payment_invalid_method(self, client):
        """Test processing payment with invalid payment method."""
        payment_data = {
            "order_id": 101,
            "amount": 99.99,
            "method": "invalid_method"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "Invalid payment method" in error["detail"]

    def test_process_payment_valid_methods(self, client):
        """Test processing payments with all valid methods."""
        valid_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
        
        for method in valid_methods:
            payment_data = {
                "order_id": 101,
                "amount": 25.0,
                "method": method
            }
            
            response = client.post("/api/v1/payments", json=payment_data)
            # Some might fail due to gateway simulation, but shouldn't be validation errors
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
            
            if response.status_code == status.HTTP_201_CREATED:
                payment = response.json()
                assert payment["method"] == method

    def test_get_payment_by_id_existing(self, client):
        """Test getting an existing payment by ID."""
        # First create a payment
        payment_data = {
            "order_id": 101,
            "amount": 50.0,
            "method": "credit_card"
        }
        
        create_response = client.post("/api/v1/payments", json=payment_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            created_payment = create_response.json()
            payment_id = created_payment["id"]
            
            # Get the payment
            response = client.get(f"/api/v1/payments/{payment_id}")
            assert response.status_code == status.HTTP_200_OK
            
            payment = response.json()
            assert payment["id"] == payment_id
            assert payment["order_id"] == payment_data["order_id"]

    def test_get_payment_by_id_nonexistent(self, client):
        """Test getting a non-existent payment by ID."""
        response = client.get("/api/v1/payments/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error = response.json()
        assert "not found" in error["detail"].lower()

    def test_get_payments_by_order_existing(self, client):
        """Test getting payments for an existing order."""
        response = client.get("/api/v1/payments/order/101")
        assert response.status_code == status.HTTP_200_OK
        
        payments = response.json()
        assert isinstance(payments, list)
        # All payments should belong to order 101
        for payment in payments:
            assert payment["order_id"] == 101

    def test_get_payments_by_order_no_payments(self, client):
        """Test getting payments for order with no payments."""
        response = client.get("/api/v1/payments/order/999")
        assert response.status_code == status.HTTP_200_OK
        
        payments = response.json()
        assert isinstance(payments, list)
        assert len(payments) == 0

    def test_refund_payment_valid(self, client):
        """Test refunding a valid payment."""
        # First create a payment
        payment_data = {
            "order_id": 101,
            "amount": 100.0,
            "method": "credit_card"
        }
        
        create_response = client.post("/api/v1/payments", json=payment_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            created_payment = create_response.json()
            payment_id = created_payment["id"]
            
            # Refund the payment
            refund_data = {
                "amount": 50.0,
                "reason": "defective_product"
            }
            
            response = client.post(f"/api/v1/payments/{payment_id}/refund", json=refund_data)
            assert response.status_code == status.HTTP_201_CREATED
            
            refund = response.json()
            assert "id" in refund
            assert refund["original_payment_id"] == payment_id
            assert refund["amount"] == refund_data["amount"]
            assert refund["reason"] == refund_data["reason"]
            assert refund["status"] == "completed"

    def test_refund_payment_full_refund(self, client):
        """Test full refund of a payment (no amount specified)."""
        # First create a payment
        payment_data = {
            "order_id": 101,
            "amount": 75.0,
            "method": "paypal"
        }
        
        create_response = client.post("/api/v1/payments", json=payment_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            created_payment = create_response.json()
            payment_id = created_payment["id"]
            
            # Full refund (no amount specified)
            refund_data = {
                "reason": "order_cancelled"
            }
            
            response = client.post(f"/api/v1/payments/{payment_id}/refund", json=refund_data)
            assert response.status_code == status.HTTP_201_CREATED
            
            refund = response.json()
            assert refund["amount"] == payment_data["amount"]  # Should be full amount

    def test_refund_payment_nonexistent(self, client):
        """Test refunding a non-existent payment."""
        refund_data = {
            "amount": 25.0,
            "reason": "test_refund"
        }
        
        response = client.post("/api/v1/payments/999/refund", json=refund_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_refund_payment_excessive_amount(self, client):
        """Test refunding more than the original payment amount."""
        # First create a payment
        payment_data = {
            "order_id": 101,
            "amount": 50.0,
            "method": "credit_card"
        }
        
        create_response = client.post("/api/v1/payments", json=payment_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            created_payment = create_response.json()
            payment_id = created_payment["id"]
            
            # Try to refund more than original amount
            refund_data = {
                "amount": 100.0,  # More than the 50.0 original
                "reason": "test_excessive_refund"
            }
            
            response = client.post(f"/api/v1/payments/{payment_id}/refund", json=refund_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            error = response.json()
            assert "cannot exceed original payment amount" in error["detail"]

    def test_payment_workflow_complete(self, client):
        """Test complete payment workflow: process, retrieve, refund."""
        # Process payment
        payment_data = {
            "order_id": 101,
            "amount": 120.0,
            "method": "credit_card"
        }
        
        create_response = client.post("/api/v1/payments", json=payment_data)
        if create_response.status_code == status.HTTP_201_CREATED:
            created_payment = create_response.json()
            payment_id = created_payment["id"]
            
            # Retrieve payment
            get_response = client.get(f"/api/v1/payments/{payment_id}")
            assert get_response.status_code == status.HTTP_200_OK
            retrieved_payment = get_response.json()
            assert retrieved_payment["id"] == payment_id
            
            # Partial refund
            refund_data = {
                "amount": 30.0,
                "reason": "partial_return"
            }
            
            refund_response = client.post(f"/api/v1/payments/{payment_id}/refund", json=refund_data)
            assert refund_response.status_code == status.HTTP_201_CREATED
            refund = refund_response.json()
            assert refund["amount"] == 30.0

    def test_payment_processing_fees(self, client):
        """Test that processing fees are calculated correctly."""
        payment_data = {
            "order_id": 101,
            "amount": 100.0,
            "method": "credit_card"
        }
        
        response = client.post("/api/v1/payments", json=payment_data)
        if response.status_code == status.HTTP_201_CREATED:
            payment = response.json()
            
            # Processing fee should be around 2.9% (2.90 for 100.0)
            expected_fee = round(100.0 * 0.029, 2)
            assert payment["processing_fee"] == expected_fee
            
            # Net amount should be amount minus fee
            expected_net = 100.0 - expected_fee
            assert payment["net_amount"] == expected_net