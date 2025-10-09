#!/bin/bash

# Setup Kibana index patterns and dashboards for FastAPI logging

set -e

KIBANA_URL="http://localhost:5601"
ELASTICSEARCH_URL="http://localhost:9200"

echo "Setting up Kibana for FastAPI logging..."

# Wait for Kibana to be ready
echo "Waiting for Kibana to be ready..."
until curl -s "$KIBANA_URL/api/status" > /dev/null; do
    echo "Waiting for Kibana..."
    sleep 5
done

echo "Kibana is ready!"

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch to be ready..."
until curl -s "$ELASTICSEARCH_URL/_cluster/health" > /dev/null; do
    echo "Waiting for Elasticsearch..."
    sleep 5
done

echo "Elasticsearch is ready!"

# Create index pattern for FastAPI logs
echo "Creating index pattern for FastAPI logs..."
curl -X POST "$KIBANA_URL/api/saved_objects/index-pattern/fastapi-logs-*" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "fastapi-logs-*",
      "timeFieldName": "@timestamp"
    }
  }' || echo "Index pattern may already exist"

# Set default index pattern
echo "Setting default index pattern..."
curl -X POST "$KIBANA_URL/api/kibana/settings/defaultIndex" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "value": "fastapi-logs-*"
  }' || true

# Create some sample searches
echo "Creating sample saved searches..."

# Error logs search
curl -X POST "$KIBANA_URL/api/saved_objects/search" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "FastAPI Error Logs",
      "description": "Show all error and warning logs",
      "hits": 0,
      "columns": ["@timestamp", "level", "message", "event", "logger"],
      "sort": [["@timestamp", "desc"]],
      "version": 1,
      "kibanaSavedObjectMeta": {
        "searchSourceJSON": "{\"index\":\"fastapi-logs-*\",\"query\":{\"match\":{\"level\":{\"query\":\"ERROR WARNING\",\"type\":\"phrase\"}}},\"filter\":[]}"
      }
    }
  }' || true

# Request logs search
curl -X POST "$KIBANA_URL/api/saved_objects/search" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "FastAPI Request Logs",
      "description": "Show all HTTP request logs",
      "hits": 0,
      "columns": ["@timestamp", "method", "url", "status_code", "duration_seconds", "client_ip"],
      "sort": [["@timestamp", "desc"]],
      "version": 1,
      "kibanaSavedObjectMeta": {
        "searchSourceJSON": "{\"index\":\"fastapi-logs-*\",\"query\":{\"match\":{\"event\":{\"query\":\"request_start request_end\",\"type\":\"phrase\"}}},\"filter\":[]}"
      }
    }
  }' || true

# User activity search
curl -X POST "$KIBANA_URL/api/saved_objects/search" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "User Activity Logs",
      "description": "Show user-related activities",
      "hits": 0,
      "columns": ["@timestamp", "event", "user_id", "user_name", "message"],
      "sort": [["@timestamp", "desc"]],
      "version": 1,
      "kibanaSavedObjectMeta": {
        "searchSourceJSON": "{\"index\":\"fastapi-logs-*\",\"query\":{\"bool\":{\"should\":[{\"wildcard\":{\"event\":\"*user*\"}},{\"wildcard\":{\"event\":\"*order*\"}}]}},\"filter\":[]}"
      }
    }
  }' || true

echo ""
echo "Kibana setup complete!"
echo ""
echo "Available saved searches:"
echo "  - FastAPI Error Logs: Shows all errors and warnings"
echo "  - FastAPI Request Logs: Shows HTTP request/response logs"
echo "  - User Activity Logs: Shows user and order related activities"
echo ""
echo "Access Kibana at: $KIBANA_URL"
echo "Go to Discover tab to start exploring your logs!"
echo ""
echo "Useful Kibana queries:"
echo "  - level:ERROR                    # Show only errors"
echo "  - event:request_end              # Show completed requests"
echo "  - status_code:>=400              # Show failed requests"
echo "  - duration_seconds:>1            # Show slow requests"
echo "  - user_id:1                      # Show logs for specific user"
echo "  - message:*exception*            # Search in log messages"