#!/usr/bin/env python3
"""Test script to verify FastAPI server context manager works correctly."""

import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests  # noqa: E402

from tests.conftest import FastAPIServerManager  # noqa: E402


def test_context_manager():
    """Test that the FastAPI context manager works correctly."""
    print("Testing FastAPI Server Context Manager")
    print("=" * 40)

    # Test server startup and shutdown
    print("\n1. Testing server startup...")

    try:
        with FastAPIServerManager(host="127.0.0.1", port=8000):
            print("Server started successfully")

            # Test if server is responding
            print("\n2. Testing server response...")
            response = requests.get("http://127.0.0.1:8000/health", timeout=5)

            if response.status_code == 200:
                print("Server is responding to health checks")
                print(f"Response: {response.json()}")
            else:
                print(f"Server returned status code: {response.status_code}")
                return False

            # Test API endpoints
            print("\n3. Testing API endpoints...")
            endpoints_to_test = ["/api/v1/users", "/api/v1/orders"]

            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(endpoint, timeout=5)
                    print(f"{endpoint}: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Warning - {endpoint}: {e}")

            print("\n4. Testing server will auto-stop when exiting context...")

        time.sleep(0.5)  # Small delay to ensure cleanup

        print("Server stopped successfully")

        # Verify server is actually stopped
        print("\n4. Verifying server shutdown...")
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=2)
            print("Error: Server is still running (this shouldn't happen)")
            return False
        except requests.exceptions.RequestException:
            print("Server is properly stopped")
            return True

        return True

    except Exception as e:
        print(f"Error during testing: {e}")
        return False


if __name__ == "__main__":
    success = test_context_manager()

    print("\n" + "=" * 40)
    if success:
        print("All tests passed! Context manager is working correctly.")
        sys.exit(0)
    else:
        print("Tests failed! Please check the implementation.")
        sys.exit(1)
