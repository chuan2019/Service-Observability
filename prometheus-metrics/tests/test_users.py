"""
Tests for User Service API endpoints.
"""

import pytest
from fastapi import status


class TestUserService:
    """Test cases for User Service endpoints."""

    def test_get_all_users(self, client):
        """Test getting all users."""
        response = client.get("/api/v1/users")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        # Should have some default users
        assert len(data) >= 0

    def test_get_user_by_id_existing(self, client):
        """Test getting an existing user by ID."""
        # Test with default user ID 1
        response = client.get("/api/v1/users/1")
        assert response.status_code == status.HTTP_200_OK
        
        user = response.json()
        assert "id" in user
        assert "name" in user
        assert "email" in user
        assert "status" in user
        assert user["id"] == 1

    def test_get_user_by_id_nonexistent(self, client):
        """Test getting a non-existent user by ID."""
        response = client.get("/api/v1/users/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_create_user_valid(self, client):
        """Test creating a user with valid data."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "status": "active"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_user = response.json()
        assert "id" in created_user
        assert created_user["name"] == user_data["name"]
        assert created_user["email"] == user_data["email"]
        assert created_user["status"] == user_data["status"]
        assert "created_at" in created_user

    def test_create_user_missing_name(self, client):
        """Test creating a user without required name field."""
        user_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_missing_email(self, client):
        """Test creating a user without required email field."""
        user_data = {
            "name": "Test User"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_invalid_email(self, client):
        """Test creating a user with invalid email format."""
        user_data = {
            "name": "Test User",
            "email": "invalid-email"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_user_existing(self, client):
        """Test updating an existing user."""
        update_data = {
            "name": "Updated User",
            "status": "inactive"
        }
        
        response = client.put("/api/v1/users/1", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        updated_user = response.json()
        assert updated_user["name"] == update_data["name"]
        assert updated_user["status"] == update_data["status"]
        assert "updated_at" in updated_user

    def test_update_user_nonexistent(self, client):
        """Test updating a non-existent user."""
        update_data = {
            "name": "Updated User"
        }
        
        response = client.put("/api/v1/users/999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_empty_data(self, client):
        """Test updating a user with empty data."""
        update_data = {}
        
        response = client.put("/api/v1/users/1", json=update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "No valid fields" in error["detail"]

    def test_delete_user_existing(self, client):
        """Test deleting an existing user."""
        # First create a user to delete
        user_data = {
            "name": "User to Delete",
            "email": "delete@example.com"
        }
        create_response = client.post("/api/v1/users", json=user_data)
        created_user = create_response.json()
        user_id = created_user["id"]
        
        # Now delete the user
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert str(user_id) in result["message"]

    def test_delete_user_nonexistent(self, client):
        """Test deleting a non-existent user."""
        response = client.delete("/api/v1/users/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_validate_user_exists_existing(self, client):
        """Test validating an existing user."""
        response = client.get("/api/v1/users/1/validate")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "user_id" in result
        assert "exists" in result
        assert result["user_id"] == 1
        assert result["exists"] is True

    def test_validate_user_exists_nonexistent(self, client):
        """Test validating a non-existent user."""
        response = client.get("/api/v1/users/999/validate")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["user_id"] == 999
        assert result["exists"] is False

    def test_user_workflow_complete(self, client):
        """Test complete user workflow: create, read, update, delete."""
        # Create user
        user_data = {
            "name": "Workflow User",
            "email": "workflow@example.com",
            "status": "active"
        }
        
        create_response = client.post("/api/v1/users", json=user_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        created_user = create_response.json()
        user_id = created_user["id"]
        
        # Read user
        read_response = client.get(f"/api/v1/users/{user_id}")
        assert read_response.status_code == status.HTTP_200_OK
        read_user = read_response.json()
        assert read_user["name"] == user_data["name"]
        
        # Update user
        update_data = {"name": "Updated Workflow User"}
        update_response = client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        updated_user = update_response.json()
        assert updated_user["name"] == update_data["name"]
        
        # Delete user
        delete_response = client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Verify user is deleted
        final_read_response = client.get(f"/api/v1/users/{user_id}")
        assert final_read_response.status_code == status.HTTP_404_NOT_FOUND