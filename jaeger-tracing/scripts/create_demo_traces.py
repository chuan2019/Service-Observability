#!/usr/bin/env python3
"""
Simplified script to create sample trace data in Elasticsearch for Kibana.
"""

import random
import time
import uuid
from datetime import datetime, timedelta

import requests

ELASTICSEARCH_URL = "http://localhost:9200"


def create_simple_traces():
    """Create simple trace documents that will work with Elasticsearch."""

    # Create a simple index with basic mapping
    index_name = "jaeger-traces-demo"

    # Simple mapping
    mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "traceId": {"type": "keyword"},
                "spanId": {"type": "keyword"},
                "service": {"type": "keyword"},
                "operation": {"type": "text"},
                "duration_ms": {"type": "integer"},
                "status_code": {"type": "integer"},
                "method": {"type": "keyword"},
                "error": {"type": "boolean"},
            }
        }
    }

    # Delete if exists and create new
    requests.delete(f"{ELASTICSEARCH_URL}/{index_name}")
    response = requests.put(f"{ELASTICSEARCH_URL}/{index_name}", json=mapping)

    if response.status_code in [200, 201]:
        print(f"✅ Created index: {index_name}")
    else:
        print(f"❌ Failed to create index: {response.text}")
        return None

    return index_name


def generate_simple_trace_data():
    """Generate simple trace data for demonstration."""

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
    ]
    methods = ["GET", "POST", "PUT", "DELETE"]
    status_codes = [200, 201, 400, 404, 500]

    traces = []

    for i in range(50):
        trace_id = str(uuid.uuid4())
        timestamp = datetime.now() - timedelta(
            minutes=random.randint(1, 1440)
        )  # Last 24 hours

        trace = {
            "timestamp": timestamp.isoformat(),
            "traceId": trace_id,
            "spanId": str(uuid.uuid4()),
            "service": random.choice(services),
            "operation": random.choice(operations),
            "duration_ms": random.randint(1, 2000),
            "status_code": random.choice(status_codes),
            "method": random.choice(methods),
            "error": random.choice([True, False]),
        }

        traces.append(trace)

    return traces


def push_simple_traces(index_name, traces):
    """Push simple trace data to Elasticsearch."""

    print(f"📤 Pushing {len(traces)} traces to Elasticsearch...")

    success_count = 0
    for trace in traces:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{index_name}/_doc",
            json=trace,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code in [200, 201]:
            success_count += 1

    print(f"✅ Successfully indexed {success_count}/{len(traces)} traces")
    return success_count > 0


def create_kibana_index_pattern(index_name):
    """Create Kibana index pattern."""

    kibana_url = "http://localhost:5601"

    # Create index pattern
    index_pattern_data = {
        "attributes": {"title": f"{index_name}*", "timeFieldName": "timestamp"}
    }

    response = requests.post(
        f"{kibana_url}/api/saved_objects/index-pattern/{index_name}",
        json=index_pattern_data,
        headers={"Content-Type": "application/json", "kbn-xsrf": "true"},
    )

    if response.status_code in [200, 201]:
        print(f"✅ Created Kibana index pattern for {index_name}")
    else:
        print("⚠️  Index pattern might already exist or failed to create")


def main():
    """Main function."""

    print("🚀 Setting up simple trace data for Kibana integration...")

    # Create index and data
    index_name = create_simple_traces()
    if not index_name:
        return

    traces = generate_simple_trace_data()

    if push_simple_traces(index_name, traces):
        # Wait for indexing
        print("⏳ Waiting for data to be indexed...")
        time.sleep(3)

        # Create Kibana index pattern
        create_kibana_index_pattern(index_name)

        # Verify data
        response = requests.get(f"{ELASTICSEARCH_URL}/{index_name}/_search")
        if response.status_code == 200:
            result = response.json()
            total = result["hits"]["total"]["value"]
            print(f"✅ Found {total} traces in Elasticsearch")

        print("\n🎉 Setup complete!")
        print("\n📊 Kibana Integration Guide:")
        print("1. Visit Kibana at: http://localhost:5601")
        print("2. Go to 'Stack Management' → 'Index Patterns'")
        print(f"3. Create or select '{index_name}*' index pattern")
        print("4. Set 'timestamp' as time field")
        print("5. Go to 'Discover' to explore trace data")
        print("\n🔍 Sample queries in Kibana:")
        print('   - service: "fastapi-jaeger-demo"')
        print("   - status_code: 500")
        print("   - error: true")
        print("   - duration_ms: >1000")
        print('   - method: "POST"')

    else:
        print("❌ Failed to push traces to Elasticsearch")


if __name__ == "__main__":
    main()
