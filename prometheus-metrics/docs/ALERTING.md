# Prometheus Alerting Configuration

This directory contains the alerting configuration for the microservices monitoring setup.

## Files

- **prometheus-microservices.yml**: Main Prometheus configuration with alerting section
- **alert_rules.yml**: Alert rules definitions for all services

## Alert Groups

### 1. Service Availability
- **ServiceDown**: Triggers when any service is down for more than 1 minute
- **ServiceHighErrorRate**: Triggers when error rate exceeds 5% for 5 minutes

### 2. Service Performance
- **HighLatency**: Warning when 95th percentile latency exceeds 1 second
- **VeryHighLatency**: Critical alert when 95th percentile latency exceeds 3 seconds

### 3. Inventory-Specific Alerts
- **LowStockLevel**: Warning when stock falls below 10 units
- **CriticalStockLevel**: Critical alert when stock falls below 5 units
- **InventoryOperationFailureRate**: Triggers when operation failure rate exceeds 10%

### 4. Order Service Alerts
- **HighOrderFailureRate**: Triggers when order operation failure rate exceeds 10%

### 5. Payment Service Alerts
- **HighPaymentFailureRate**: Critical alert when payment failure rate exceeds 5%

### 6. System Resource Alerts
- **HighRequestsInProgress**: Warning when service has more than 100 concurrent requests
- **PrometheusTargetDown**: Critical alert when Prometheus itself is down

### 7. Database Alerts
- **PostgresDown**: Critical alert when PostgreSQL is unavailable

### 8. API Gateway Alerts
- **HighGatewayErrorRate**: Warning when gateway error rate exceeds 5%
- **HighGatewayTraffic**: Warning when gateway handles more than 1000 req/s

## Alert Severity Levels

- **Critical**: Requires immediate attention (service down, database down, very high latency)
- **Warning**: Should be investigated soon (high error rate, performance degradation)

## Testing Alerts

### View Active Alerts in Prometheus UI
1. Navigate to `http://localhost:9090/alerts`
2. Check the status of all configured alerts

### Reload Configuration
After modifying alert rules, reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

Or restart the Prometheus container:
```bash
docker-compose -f docker-compose.microservices.yml restart prometheus
```

### Verify Alert Rules
Check if alert rules are loaded correctly:
```bash
curl http://localhost:9090/api/v1/rules
```

## Setting Up Alertmanager (Optional)

To actually send notifications (email, Slack, PagerDuty, etc.), you need to set up Alertmanager:

### 1. Create `alertmanager.yml` configuration:
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

receivers:
  - name: 'default'
    # Configure your notification channels here
    # Examples: email_configs, slack_configs, pagerduty_configs, etc.

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
```

### 2. Add Alertmanager to `docker-compose.microservices.yml`:
```yaml
  alertmanager:
    image: prom/alertmanager:v0.26.0
    ports:
      - "9093:9093"
    volumes:
      - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - microservices
```

### 3. Uncomment the Alertmanager target in `prometheus-microservices.yml`:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'  # Uncomment this line
```

## Testing Alert Rules

### Trigger a Test Alert

1. **Stop a service** to trigger `ServiceDown`:
   ```bash
   docker-compose -f docker-compose.microservices.yml stop user-service
   ```
   Wait 1 minute and check Prometheus alerts.

2. **Generate high load** to trigger latency alerts:
   ```bash
   make load-test
   ```

3. **Create low stock** to trigger inventory alerts:
   ```bash
   # Create a product with low stock through the API
   curl -X POST http://localhost:8000/api/inventory \
     -H "Content-Type: application/json" \
     -d '{"product_id": 999, "available_quantity": 3, "reserved_quantity": 0, "reorder_level": 10}'
   ```

## Monitoring Alert Status

### Prometheus UI
- Active Alerts: `http://localhost:9090/alerts`
- Alert Rules: `http://localhost:9090/rules`

### Query Alert States
```promql
# Count alerts by severity
ALERTS{severity="critical"}
ALERTS{severity="warning"}

# Check specific alert
ALERTS{alertname="ServiceDown"}
```

## Customizing Alerts

### Adjust Thresholds
Edit `alert_rules.yml` and modify the expression thresholds:
- Error rates: Change `> 0.05` (5%) to your desired threshold
- Latency: Change `> 1` (1 second) to your desired threshold
- Stock levels: Change `< 10` to your desired threshold

### Add New Alerts
Add new rules to the appropriate group in `alert_rules.yml`:
```yaml
- alert: YourAlertName
  expr: your_prometheus_query > threshold
  for: 5m
  labels:
    severity: warning
    category: custom
  annotations:
    summary: "Brief description"
    description: "Detailed description with {{ $value }}"
```

### Reload After Changes
```bash
docker-compose -f docker-compose.microservices.yml restart prometheus
```

## Best Practices

1. **Start with Warning alerts** before making them Critical
2. **Use appropriate evaluation periods** (`for: 5m`) to avoid flapping
3. **Add meaningful annotations** with context and values
4. **Group related alerts** using labels
5. **Test alerts regularly** to ensure they work as expected
6. **Document runbooks** for each critical alert

## Troubleshooting

### Alerts not showing up
- Check Prometheus logs: `docker logs prometheus-metrics-prometheus-1`
- Verify rule file syntax: Visit `http://localhost:9090/rules`
- Check configuration is loaded: `http://localhost:9090/config`

### Alert rules syntax errors
- Validate YAML syntax
- Test PromQL expressions in Prometheus UI
- Check for proper indentation and labels

### False positives
- Adjust evaluation period (`for` duration)
- Refine query expressions
- Add inhibition rules (requires Alertmanager)

## Resources

- [Prometheus Alerting Documentation](https://prometheus.io/docs/alerting/latest/overview/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PromQL Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
