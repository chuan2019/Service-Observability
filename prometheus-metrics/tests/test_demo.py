"""
Tests for Demo Service API endpoints.
"""

import pytest
from fastapi import status


class TestDemoService:
    """Test cases for Demo Service endpoints."""

    def test_demo_full_flow_existing_user(self, client):
        """Test demo full flow with existing user."""
        response = client.get("/api/v1/demo/full-flow/1")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "flow_status" in result
        assert result["flow_status"] == "completed"
        assert "user" in result
        assert "order" in result
        assert "payment" in result
        assert "summary" in result
        
        # Check that user ID matches
        assert result["user"]["id"] == 1
        assert result["summary"]["user_id"] == 1
        
        # Check that order was created for the user
        assert result["order"]["user_id"] == 1
        
        # Check that payment was processed for the order
        assert result["payment"]["order_id"] == result["order"]["id"]

    def test_demo_full_flow_nonexistent_user(self, client):
        """Test demo full flow with non-existent user."""
        response = client.get("/api/v1/demo/full-flow/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error = response.json()
        assert "not found" in error["detail"].lower()

    def test_simulate_user_journey(self, client):
        """Test user journey simulation."""
        response = client.post("/api/v1/demo/simulate-user-journey")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "journey_status" in result
        assert result["journey_status"] == "completed"
        assert "steps_completed" in result
        assert result["steps_completed"] == 4
        assert "user" in result
        assert "order" in result
        assert "payment" in result
        assert "metrics_recorded" in result
        
        # Verify all steps were recorded
        metrics = result["metrics_recorded"]
        assert metrics["user_created"] is True
        assert metrics["order_processed"] is True
        assert metrics["payment_completed"] is True
        assert metrics["order_completed"] is True
        
        # Verify data consistency
        assert result["order"]["user_id"] == result["user"]["id"]
        assert result["payment"]["order_id"] == result["order"]["id"]
        assert result["order"]["status"] == "completed"
        assert result["payment"]["status"] == "completed"

    def test_stress_test(self, client):
        """Test stress test endpoint."""
        response = client.get("/api/v1/demo/stress-test")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "operations_performed" in result
        assert "metrics_generated" in result
        assert "test_summary" in result
        
        assert result["metrics_generated"] is True
        assert isinstance(result["operations_performed"], list)
        assert len(result["operations_performed"]) > 0
        
        # Check test summary
        summary = result["test_summary"]
        assert "total_operations" in summary
        assert "user_operations" in summary
        assert "order_operations" in summary
        assert "payment_operations" in summary
        assert "cache_operations" in summary
        
        # Verify operation counts
        assert summary["total_operations"] > 0
        assert summary["cache_operations"] == 5  # Fixed number in implementation

    def test_demo_endpoints_generate_metrics(self, client):
        """Test that demo endpoints generate metrics."""
        # Run demo operations
        client.get("/api/v1/demo/full-flow/1")
        client.post("/api/v1/demo/simulate-user-journey")
        client.get("/api/v1/demo/stress-test")
        
        # Check metrics endpoint
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK
        
        metrics_content = metrics_response.text
        
        # Should contain service-specific metrics
        assert "user_service_operations_total" in metrics_content
        assert "order_service_operations_total" in metrics_content
        assert "payment_service_operations_total" in metrics_content

    def test_demo_full_flow_data_consistency(self, client):
        """Test data consistency in full flow demo."""
        response = client.get("/api/v1/demo/full-flow/2")
        
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            
            # User data consistency
            user = result["user"]
            assert user["id"] == 2
            assert "name" in user
            assert "email" in user
            
            # Order data consistency
            order = result["order"]
            assert order["user_id"] == user["id"]
            assert order["amount"] > 0
            assert len(order["items"]) > 0
            assert order["type"] == "express"
            
            # Payment data consistency
            payment = result["payment"]
            assert payment["order_id"] == order["id"]
            assert payment["amount"] == order["amount"]
            assert payment["method"] == "credit_card"
            assert payment["status"] == "completed"
            
            # Summary consistency
            summary = result["summary"]
            assert summary["user_id"] == user["id"]
            assert summary["user_name"] == user["name"]
            assert summary["order_id"] == order["id"]
            assert summary["order_amount"] == order["amount"]
            assert summary["payment_id"] == payment["id"]
            assert summary["payment_status"] == payment["status"]

    def test_simulate_user_journey_creates_unique_users(self, client):
        """Test that user journey simulation creates unique users."""
        # Run multiple simulations
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/demo/simulate-user-journey")
            if response.status_code == status.HTTP_200_OK:
                responses.append(response.json())
        
        # Check that different users were created
        user_ids = [r["user"]["id"] for r in responses]
        user_emails = [r["user"]["email"] for r in responses]
        
        # All user IDs should be different
        assert len(set(user_ids)) == len(user_ids)
        
        # All emails should be different
        assert len(set(user_emails)) == len(user_emails)

    def test_stress_test_covers_all_services(self, client):
        """Test that stress test covers all services."""
        response = client.get("/api/v1/demo/stress-test")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        operations = result["operations_performed"]
        
        # Should have operations for all services
        has_user_ops = any("user" in op.lower() for op in operations)
        has_order_ops = any("order" in op.lower() for op in operations)
        has_payment_ops = any("payment" in op.lower() for op in operations)
        
        assert has_user_ops, "Stress test should include user operations"
        assert has_order_ops, "Stress test should include order operations"  
        assert has_payment_ops, "Stress test should include payment operations"

    def test_demo_error_handling(self, client):
        """Test error handling in demo endpoints."""
        # Test with invalid user ID (string instead of int)
        response = client.get("/api/v1/demo/full-flow/invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_demo_performance_reasonable(self, client):
        """Test that demo endpoints complete in reasonable time."""
        import time
        
        # Test full flow performance
        start_time = time.time()
        response = client.get("/api/v1/demo/full-flow/1")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        # Should complete within 5 seconds (allowing for simulated delays)
        assert (end_time - start_time) < 5.0
        
        # Test user journey performance
        start_time = time.time()
        response = client.post("/api/v1/demo/simulate-user-journey")
        end_time = time.time()
        
        if response.status_code == status.HTTP_200_OK:
            # Should complete within 10 seconds
            assert (end_time - start_time) < 10.0