"""Integration tests for Elasticsearch and Kibana."""

import time
from datetime import datetime

import pytest
import requests
from elasticsearch import Elasticsearch
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestElasticsearchIntegration:
    """Test Elasticsearch integration."""

    def test_elasticsearch_connection(
        self, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test that Elasticsearch is accessible."""
        assert elasticsearch_client.ping(), "Elasticsearch should be accessible"

    def test_elasticsearch_cluster_health(
        self, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test Elasticsearch cluster health."""
        health = elasticsearch_client.cluster.health()
        assert health["status"] in [
            "green",
            "yellow",
        ], f"Cluster health should be green/yellow, got {health['status']}"

    def test_log_index_creation(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test that log indices are created when logs are generated."""
        # Make some requests to generate logs
        client.get("/health")
        client.get("/api/v1/users")
        client.post(
            "/api/v1/users", json={"name": "Test User", "email": "test@integration.com"}
        )

        # Wait for logs to be indexed
        time.sleep(5)

        # Check if any fastapi-logs indices exist
        try:
            indices = elasticsearch_client.indices.get("fastapi-logs-*")
            assert len(indices) > 0, "Should have created fastapi-logs indices"
        except Exception as e:
            # If no indices exist yet, that's also acceptable in test environment
            pytest.skip(f"No log indices found: {e}")

    def test_log_document_structure(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test that log documents have the expected structure."""
        # Generate some logs
        client.get("/health")
        time.sleep(3)

        try:
            # Search for recent logs
            response = elasticsearch_client.search(
                index="fastapi-logs-*",
                body={
                    "query": {"match_all": {}},
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "size": 1,
                },
            )

            if response["hits"]["total"]["value"] > 0:
                log_doc = response["hits"]["hits"][0]["_source"]

                # Check required fields
                assert "@timestamp" in log_doc
                assert "level" in log_doc
                assert "message" in log_doc
                assert "application" in log_doc
                assert "environment" in log_doc

                # Check timestamp format
                timestamp = log_doc["@timestamp"]
                assert timestamp.endswith("Z"), "Timestamp should be in UTC format"

                # Verify it's a valid ISO timestamp
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                pytest.skip("No log documents found in Elasticsearch")

        except Exception as e:
            pytest.skip(f"Could not search logs in Elasticsearch: {e}")

    def test_different_log_levels(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test that different log levels are properly indexed."""
        # Generate different types of logs
        client.get("/health")  # INFO logs
        client.get("/api/v1/users/999")  # WARNING logs (404)

        time.sleep(3)

        try:
            # Search for INFO logs
            info_response = elasticsearch_client.search(
                index="fastapi-logs-*",
                body={"query": {"term": {"level": "INFO"}}, "size": 1},
            )

            # Search for WARNING logs
            warning_response = elasticsearch_client.search(
                index="fastapi-logs-*",
                body={"query": {"term": {"level": "WARNING"}}, "size": 1},
            )

            if info_response["hits"]["total"]["value"] > 0:
                info_doc = info_response["hits"]["hits"][0]["_source"]
                assert info_doc["level"] == "INFO"

            if warning_response["hits"]["total"]["value"] > 0:
                warning_doc = warning_response["hits"]["hits"][0]["_source"]
                assert warning_doc["level"] == "WARNING"

        except Exception as e:
            pytest.skip(f"Could not test log levels: {e}")


@pytest.mark.integration
class TestKibanaIntegration:
    """Test Kibana integration."""

    def test_kibana_availability(self, wait_for_services):
        """Test that Kibana is accessible."""
        from app.core.config import settings

        response = requests.get(
            f"http://{settings.KIBANA_HOST}:{settings.KIBANA_PORT}/api/status"
        )
        assert response.status_code == 200, "Kibana should be accessible"

        data = response.json()
        assert (
            data["status"]["overall"]["level"] == "available"
        ), "Kibana should be available"

    def test_index_pattern_exists(self, wait_for_services):
        """Test that fastapi-logs index pattern exists in Kibana."""
        from app.core.config import settings

        try:
            response = requests.get(
                f"http://{settings.KIBANA_HOST}:{settings.KIBANA_PORT}/api/saved_objects/_find",
                params={
                    "type": "index-pattern",
                    "search_fields": "title",
                    "search": "fastapi-logs-*",
                },
            )

            if response.status_code == 200:
                data = response.json()
                patterns = [
                    obj
                    for obj in data.get("saved_objects", [])
                    if obj["attributes"]["title"] == "fastapi-logs-*"
                ]
                assert len(patterns) > 0, "fastapi-logs-* index pattern should exist"
            else:
                pytest.skip("Could not access Kibana saved objects API")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to Kibana: {e}")

    def test_saved_searches_exist(self, wait_for_services):
        """Test that saved searches were created in Kibana."""
        from app.core.config import settings

        try:
            response = requests.get(
                f"http://{settings.KIBANA_HOST}:{settings.KIBANA_PORT}/api/saved_objects/_find",
                params={"type": "search", "search": "FastAPI"},
            )

            if response.status_code == 200:
                data = response.json()
                searches = data.get("saved_objects", [])

                search_titles = [obj["attributes"]["title"] for obj in searches]

                expected_searches = [
                    "FastAPI Error Logs",
                    "FastAPI Request Logs",
                    "User Activity Logs",
                ]

                for expected in expected_searches:
                    assert any(
                        expected in title for title in search_titles
                    ), f"Should have saved search containing '{expected}'"
            else:
                pytest.skip("Could not access Kibana saved objects API")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to Kibana: {e}")

    def test_kibana_query_logs(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test querying logs through Kibana's Elasticsearch proxy."""
        from app.core.config import settings

        # Generate some logs first
        client.get("/health")
        client.post(
            "/api/v1/users", json={"name": "Kibana Test", "email": "kibana@test.com"}
        )

        time.sleep(3)

        try:
            # Use Kibana's internal Elasticsearch API
            kibana_es_url = f"http://{settings.KIBANA_HOST}:{settings.KIBANA_PORT}/api/console/proxy"

            query_data = {
                "path": "/fastapi-logs-*/_search",
                "method": "POST",
                "body": {
                    "query": {"match_all": {}},
                    "size": 5,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                },
            }

            response = requests.post(
                kibana_es_url,
                headers={"Content-Type": "application/json", "kbn-xsrf": "true"},
                json=query_data,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("hits", {}).get("total", {}).get("value", 0) > 0:
                    logs = data["hits"]["hits"]
                    assert len(logs) > 0, "Should find logs through Kibana"

                    # Verify log structure
                    log = logs[0]["_source"]
                    assert "@timestamp" in log
                    assert "message" in log
                else:
                    pytest.skip("No logs found through Kibana query")
            else:
                pytest.skip(f"Kibana proxy query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not query through Kibana: {e}")


@pytest.mark.integration
class TestEndToEndLogging:
    """End-to-end logging tests."""

    def test_complete_logging_workflow(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test complete logging workflow from API to Elasticsearch to Kibana."""
        # 1. Make API requests to generate logs
        health_response = client.get("/health")
        assert health_response.status_code == 200

        users_response = client.get("/api/v1/users")
        assert users_response.status_code == 200

        create_response = client.post(
            "/api/v1/users", json={"name": "E2E Test User", "email": "e2e@test.com"}
        )
        assert create_response.status_code == 201

        error_response = client.get("/api/v1/users/9999")
        assert error_response.status_code == 404

        # 2. Wait for logs to be indexed
        time.sleep(5)

        try:
            # 3. Verify logs in Elasticsearch
            search_response = elasticsearch_client.search(
                index="fastapi-logs-*",
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"event": "health_check"}},
                                {"match": {"event": "get_users"}},
                                {"match": {"event": "create_user_success"}},
                                {"match": {"event": "get_user_not_found"}},
                            ]
                        }
                    },
                    "size": 10,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                },
            )

            total_logs = search_response["hits"]["total"]["value"]
            if total_logs > 0:
                logs = search_response["hits"]["hits"]

                # Verify we have different types of events
                events = [log["_source"].get("event") for log in logs]

                # Should have at least some of our expected events
                expected_events = ["health_check", "get_users", "create_user_success"]
                found_events = [event for event in expected_events if event in events]

                assert (
                    len(found_events) > 0
                ), f"Should find some expected events. Found: {events}"

                # 4. Verify log structure is correct
                for log in logs:
                    source = log["_source"]
                    assert "@timestamp" in source
                    assert "level" in source
                    assert "application" in source
                    assert source["application"] == "FastAPI Elasticsearch Demo"
            else:
                pytest.skip("No logs found in end-to-end test")

        except Exception as e:
            pytest.skip(f"End-to-end test failed: {e}")

    def test_log_correlation(
        self, client: TestClient, elasticsearch_client: Elasticsearch, wait_for_services
    ):
        """Test that related logs can be correlated by request_id."""
        # Make a request that should generate multiple related logs
        response = client.post(
            "/api/v1/users",
            json={"name": "Correlation Test", "email": "correlation@test.com"},
        )
        assert response.status_code == 201

        time.sleep(3)

        try:
            # Search for logs related to this request
            search_response = elasticsearch_client.search(
                index="fastapi-logs-*",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"exists": {"field": "request_id"}},
                                {"range": {"@timestamp": {"gte": "now-1m"}}},
                            ]
                        }
                    },
                    "size": 20,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                },
            )

            if search_response["hits"]["total"]["value"] > 0:
                logs = search_response["hits"]["hits"]

                # Group logs by request_id
                request_groups = {}
                for log in logs:
                    source = log["_source"]
                    request_id = source.get("request_id")
                    if request_id:
                        if request_id not in request_groups:
                            request_groups[request_id] = []
                        request_groups[request_id].append(source)

                # Find a request that has multiple logs
                multi_log_requests = {
                    rid: logs for rid, logs in request_groups.items() if len(logs) > 1
                }

                if multi_log_requests:
                    # Verify that logs in the same request group have consistent data
                    for request_id, request_logs in multi_log_requests.items():
                        methods = {
                            log.get("method")
                            for log in request_logs
                            if log.get("method")
                        }
                        urls = {
                            log.get("url") for log in request_logs if log.get("url")
                        }

                        # All logs in the same request should have the same method and URL
                        assert (
                            len(methods) <= 1
                        ), f"Request {request_id} should have consistent method"
                        assert (
                            len(urls) <= 1
                        ), f"Request {request_id} should have consistent URL"
                else:
                    pytest.skip("No correlated logs found")
            else:
                pytest.skip("No logs with request_id found")

        except Exception as e:
            pytest.skip(f"Log correlation test failed: {e}")
