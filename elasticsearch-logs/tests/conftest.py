"""Configuration and fixtures for pytest tests."""

import asyncio
import os
import signal
import subprocess
import time
from collections.abc import AsyncGenerator, Generator

import pytest
import requests
from elasticsearch import Elasticsearch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import settings
from app.main import app


class FastAPIServerManager:
    """Context manager for starting and stopping FastAPI server."""

    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.process = None
        self._startup_timeout = 15  # seconds to wait for startup

    def __enter__(self):
        """Start the FastAPI server."""
        print(f"Starting FastAPI server on {self.host}:{self.port}")
        # Start the FastAPI server process

        # Start the server process
        self.process = subprocess.Popen(
            [
                "uv",
                "run",
                "uvicorn",
                "app.main:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # Create new process group
            cwd=os.getcwd(),  # Ensure we're in the right directory
        )

        # Wait for server to start
        self._wait_for_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the FastAPI server."""
        if self.process:
            print("Stopping FastAPI server...")
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    print("Warning: Forcing FastAPI server shutdown...")
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait()

            except (OSError, ProcessLookupError):
                # Process already terminated
                pass

                self.process = None
            print("FastAPI server stopped")

    def _wait_for_server(self):
        """Wait for the server to be ready."""
        health_url = f"http://{self.host}:{self.port}/health"

        for _attempt in range(self._startup_timeout * 2):  # Check every 0.5 seconds
            try:
                response = requests.get(health_url, timeout=3)
                if response.status_code == 200:
                    print("FastAPI server is ready")
                    return
            except requests.exceptions.RequestException:
                pass

            time.sleep(0.5)

        # If server didn't start, kill the process and raise error
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass

        raise RuntimeError(
            f"FastAPI server failed to start within {self._startup_timeout} seconds"
        )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def fastapi_server():
    """Start and manage FastAPI server for the test session."""
    with FastAPIServerManager() as server:
        yield server


@pytest.fixture
def client(fastapi_server) -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client(fastapi_server) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def elasticsearch_client() -> Elasticsearch:
    """Create an Elasticsearch client for testing."""
    es = Elasticsearch(
        [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
    )
    return es


@pytest.fixture(scope="session")
def wait_for_services(fastapi_server):
    """Wait for all services (Elasticsearch, Kibana, FastAPI) to be ready."""
    print("Checking service availability...")

    # Wait for Elasticsearch
    print("Waiting for Elasticsearch...")
    max_retries = 30
    for _i in range(max_retries):
        try:
            response = requests.get(
                "http://localhost:9200/_cluster/health", timeout=5
            )
            if response.status_code == 200:
                print("Elasticsearch is ready")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    else:
        pytest.skip("Elasticsearch is not available")

    # Wait for Kibana
    print("Waiting for Kibana...")
    for _i in range(max_retries):
        try:
            response = requests.get(
                f"http://{settings.KIBANA_HOST}:{settings.KIBANA_PORT}/api/status"
            )
            if response.status_code == 200:
                print("Kibana is ready")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    else:
        pytest.skip("Kibana is not available")

    print("All services are ready for testing!")
    yield
    print("Service cleanup complete")


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {"name": "Test User", "email": "test@example.com"}


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {"user_id": 1, "product_name": "Test Product", "quantity": 2, "price": 29.99}


@pytest.fixture(autouse=True)
def cleanup_test_logs(elasticsearch_client):
    """Clean up test logs after each test."""
    yield
    # Clean up test indices after each test
    try:
        elasticsearch_client.indices.delete(index="fastapi-logs-*", ignore=[404])
    except Exception:
        pass  # Ignore cleanup errors
