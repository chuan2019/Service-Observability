#!/usr/bin/env python3
"""
Script to push sample trace data to Elasticsearch for Kibana visualization.
This demonstrates how to search and analyze distributed traces in Kibana.
"""

import json
import random
import time
import uuid
from datetime import datetime, timedelta

import requests

ELASTICSEARCH_URL = "http://localhost:9200"
KIBANA_URL = "http://localhost:5601"


def create_elasticsearch_index():
    """Create Elasticsearch index for Jaeger spans with proper mapping."""

    # Index mapping for Jaeger spans
    mapping = {
        "mappings": {
            "properties": {
                "traceID": {"type": "keyword"},
                "spanID": {"type": "keyword"},
                "parentSpanID": {"type": "keyword"},
                "operationName": {"type": "keyword"},
                "startTime": {"type": "date", "format": "epoch_millis"},
                "duration": {"type": "long"},
                "process": {
                    "properties": {
                        "serviceName": {"type": "keyword"},
                        "tags": {"type": "nested"},
                    }
                },
                "tags": {"type": "nested"},
                "logs": {"type": "nested"},
            }
        }
    }

    # Create index with mapping
    index_name = "jaeger-span-2025-10-09"
    response = requests.put(
        f"{ELASTICSEARCH_URL}/{index_name}",
        json=mapping,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code in [200, 201]:
        print(f"✅ Created Elasticsearch index: {index_name}")
    else:
        print(f"❌ Failed to create index: {response.text}")

    return index_name


def generate_trace_data(trace_count=10):
    """Generate sample trace data similar to what Jaeger would create."""

    traces = []
    services = [
        "fastapi-jaeger-demo",
        "user-service",
        "order-service",
        "payment-service",
    ]
    operations = [
        "GET /health",
        "POST /users",
        "GET /users/{id}",
        "POST /orders",
        "GET /orders/{id}",
        "POST /payments",
        "GET /demo/full-flow/{id}",
        "process_payment",
        "validate_user",
        "check_inventory",
    ]

    for _ in range(trace_count):
        trace_id = str(uuid.uuid4()).replace("-", "")
        start_time = datetime.now() - timedelta(minutes=random.randint(1, 60))

        # Generate spans for a single trace
        spans_in_trace = random.randint(2, 6)
        parent_span_id = None

        for span_idx in range(spans_in_trace):
            span_id = str(uuid.uuid4()).replace("-", "")[:16]
            service = random.choice(services)
            operation = random.choice(operations)

            # Calculate span timing
            span_start = start_time + timedelta(microseconds=span_idx * 1000)
            duration = random.randint(1000, 50000)  # 1-50ms in microseconds

            span = {
                "traceID": trace_id,
                "spanID": span_id,
                "parentSpanID": parent_span_id if span_idx > 0 else "",
                "operationName": operation,
                "startTime": int(span_start.timestamp() * 1000),  # milliseconds
                "duration": duration,
                "process": {
                    "serviceName": service,
                    "tags": [
                        {"key": "hostname", "value": f"{service}-host"},
                        {"key": "ip", "value": f"192.168.1.{random.randint(10, 100)}"},
                        {"key": "jaeger.version", "value": "1.50.0"},
                    ],
                },
                "tags": [
                    {
                        "key": "http.method",
                        "value": random.choice(["GET", "POST", "PUT"]),
                    },
                    {
                        "key": "http.status_code",
                        "value": random.choice([200, 201, 400, 500]),
                    },
                    {"key": "component", "value": "fastapi"},
                    {"key": "span.kind", "value": "server"},
                ],
                "logs": [
                    {
                        "timestamp": int(
                            (
                                span_start + timedelta(microseconds=duration // 2)
                            ).timestamp()
                            * 1000
                        ),
                        "fields": [
                            {"key": "event", "value": "processing request"},
                            {"key": "level", "value": "info"},
                        ],
                    }
                ],
            }

            traces.append(span)

            # Use this span as parent for next span
            if span_idx == 0:
                parent_span_id = span_id

    return traces


def push_traces_to_elasticsearch(index_name, traces):
    """Push trace data to Elasticsearch."""

    print(f"📤 Pushing {len(traces)} spans to Elasticsearch...")

    # Bulk insert
    bulk_data = []
    for trace in traces:
        # Index metadata
        bulk_data.append(json.dumps({"index": {"_index": index_name}}))
        # Document data
        bulk_data.append(json.dumps(trace))

    bulk_body = "\n".join(bulk_data) + "\n"

    response = requests.post(
        f"{ELASTICSEARCH_URL}/_bulk",
        data=bulk_body,
        headers={"Content-Type": "application/x-ndjson"},
    )

    if response.status_code == 200:
        result = response.json()
        errors = [
            item for item in result.get("items", []) if "error" in item.get("index", {})
        ]
        if errors:
            print(f"❌ Some documents failed to index: {len(errors)} errors")
        else:
            print(f"✅ Successfully indexed {len(traces)} trace spans")
    else:
        print(f"❌ Failed to push traces: {response.text}")


def verify_data_in_kibana():
    """Verify that data is available in Kibana."""

    print("\n🔍 Verifying data in Kibana...")

    # Check if index pattern exists
    response = requests.get(
        f"{KIBANA_URL}/api/saved_objects/index-pattern/jaeger-span-*",
        headers={"kbn-xsrf": "true"},
    )

    if response.status_code == 200:
        print("✅ Jaeger span index pattern exists in Kibana")
    else:
        print("❌ Index pattern not found in Kibana")

    # Search for traces
    search_query = {"query": {"match_all": {}}, "size": 5}

    response = requests.post(
        f"{ELASTICSEARCH_URL}/jaeger-span-*/_search",
        json=search_query,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        result = response.json()
        total_hits = result["hits"]["total"]["value"]
        print(f"✅ Found {total_hits} trace spans in Elasticsearch")

        if total_hits > 0:
            print("\n📋 Sample trace span:")
            sample_span = result["hits"]["hits"][0]["_source"]
            print(f"   Service: {sample_span['process']['serviceName']}")
            print(f"   Operation: {sample_span['operationName']}")
            print(f"   Trace ID: {sample_span['traceID'][:8]}...")
            print(f"   Duration: {sample_span['duration'] / 1000:.2f}ms")
    else:
        print(f"❌ Failed to search traces: {response.text}")


def main():
    """Main function to set up Kibana integration with sample trace data."""

    print("🚀 Setting up Kibana integration for Jaeger traces...")

    # Check if Elasticsearch is available
    try:
        response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health")
        if response.status_code != 200:
            print("❌ Elasticsearch is not available")
            return
        print("✅ Elasticsearch is available")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Elasticsearch")
        return

    # Check if Kibana is available
    try:
        response = requests.get(f"{KIBANA_URL}/api/status")
        if response.status_code != 200:
            print("❌ Kibana is not available")
            return
        print("✅ Kibana is available")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kibana")
        return

    # Create index and push sample data
    index_name = create_elasticsearch_index()
    traces = generate_trace_data(trace_count=20)
    push_traces_to_elasticsearch(index_name, traces)

    # Wait a moment for data to be indexed
    print("⏳ Waiting for data to be indexed...")
    time.sleep(3)

    # Verify data
    verify_data_in_kibana()

    print("\n🎉 Setup complete!")
    print("\n📊 Next steps:")
    print("1. Visit Kibana at: http://localhost:5601")
    print("2. Go to 'Discover' section")
    print("3. Select 'jaeger-span-*' index pattern")
    print("4. Explore trace data with filters and visualizations")
    print("5. Create dashboards for trace analysis")
    print("\n🔍 Sample Kibana queries to try:")
    print('   - process.serviceName: "fastapi-jaeger-demo"')
    print('   - operationName: "POST /users"')
    print('   - tags.key: "http.status_code" AND tags.value: "500"')
    print("   - duration: >10000  (spans longer than 10ms)")


if __name__ == "__main__":
    main()
