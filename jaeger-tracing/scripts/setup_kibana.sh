#!/bin/bash

# Kibana Index Pattern Setup for Jaeger Traces
# This script creates index patterns and dashboards for analyzing Jaeger traces in Kibana

KIBANA_URL="http://localhost:5601"
ELASTICSEARCH_URL="http://localhost:9200"

echo "Setting up Kibana for Jaeger trace analysis..."

# Wait for Kibana to be available
echo "Waiting for Kibana to start..."
until curl -f ${KIBANA_URL}/api/status > /dev/null 2>&1; do
    echo "Waiting for Kibana..."
    sleep 5
done

echo "Kibana is ready!"

# Wait a bit more for full initialization
sleep 10

# Create index pattern for Jaeger spans
echo "Creating index pattern for Jaeger traces..."
curl -X POST "${KIBANA_URL}/api/saved_objects/index-pattern/jaeger-span-*" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "attributes": {
      "title": "jaeger-span-*",
      "timeFieldName": "startTime"
    }
  }'

# Create index pattern for Jaeger services
curl -X POST "${KIBANA_URL}/api/saved_objects/index-pattern/jaeger-service-*" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "attributes": {
      "title": "jaeger-service-*",
      "timeFieldName": "@timestamp"
    }
  }'

echo "Index patterns created successfully!"

# Create a basic dashboard for trace analysis
echo "Creating Jaeger trace dashboard..."
curl -X POST "${KIBANA_URL}/api/saved_objects/dashboard" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "attributes": {
      "title": "Jaeger Trace Analysis",
      "description": "Dashboard for analyzing distributed traces from Jaeger",
      "panelsJSON": "[]",
      "optionsJSON": "{\"useMargins\":true,\"syncColors\":false,\"hidePanelTitles\":false}",
      "version": 1,
      "timeRestore": false,
      "kibanaSavedObjectMeta": {
        "searchSourceJSON": "{\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"
      }
    }
  }'

echo "Dashboard created successfully!"

echo "Setup complete! You can now:"
echo "1. Visit Kibana at: ${KIBANA_URL}"
echo "2. Go to Discover to explore trace data"
echo "3. Use the 'jaeger-span-*' index pattern to analyze spans"
echo "4. Visit the 'Jaeger Trace Analysis' dashboard"