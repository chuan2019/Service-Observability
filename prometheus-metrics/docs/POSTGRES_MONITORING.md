# PostgreSQL Monitoring with postgres_exporter

This document describes the PostgreSQL monitoring setup using postgres_exporter for the microservices architecture.

## Overview

PostgreSQL monitoring is now enabled using [postgres_exporter](https://github.com/prometheus-community/postgres_exporter), which exposes PostgreSQL metrics in Prometheus format.

## Components

### 1. postgres_exporter Service
- **Image**: `prometheuscommunity/postgres-exporter:v0.15.0`
- **Port**: `9187`
- **Connection**: Connects to PostgreSQL at `postgres:5432`
- **Database**: `ecommerce`

### 2. Prometheus Scraping
- **Job Name**: `postgres`
- **Target**: `postgres-exporter:9187`
- **Scrape Interval**: 10 seconds

## Deployed Configuration

### Docker Compose (`docker-compose.microservices.yml`)
```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:v0.15.0
  environment:
    DATA_SOURCE_NAME: "postgresql://postgres:password@postgres:5432/ecommerce?sslmode=disable"
  ports:
    - "9187:9187"
  networks:
    - microservices
  depends_on:
    postgres:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://localhost:9187/metrics"]
    interval: 10s
    timeout: 5s
    retries: 3
```

## Available Metrics

### Database Status
- `pg_up` - PostgreSQL server is up (1 = up, 0 = down)
- `pg_database_size_bytes` - Size of each database in bytes
- `pg_stat_database_numbackends` - Number of active connections per database

### Performance Metrics
- `pg_stat_database_tup_fetched` - Number of rows fetched
- `pg_stat_database_tup_returned` - Number of rows returned
- `pg_stat_database_tup_inserted` - Number of rows inserted
- `pg_stat_database_tup_updated` - Number of rows updated
- `pg_stat_database_tup_deleted` - Number of rows deleted
- `pg_stat_database_blk_read_time` - Time spent reading blocks
- `pg_stat_database_blk_write_time` - Time spent writing blocks

### Connection and Transaction Metrics
- `pg_stat_database_xact_commit` - Number of committed transactions
- `pg_stat_database_xact_rollback` - Number of rolled back transactions
- `pg_stat_database_conflicts` - Number of queries canceled due to conflicts
- `pg_stat_database_deadlocks` - Number of deadlocks detected

### Table Statistics
- `pg_stat_database_n_dead_tup` - Number of dead tuples (needs VACUUM)
- `pg_stat_database_n_live_tup` - Number of live tuples

### Replication (if configured)
- `pg_replication_lag` - Replication lag in seconds

## Active Alerts

### 1. PostgresDown (Critical)
- **Trigger**: PostgreSQL exporter is unreachable for more than 1 minute
- **Impact**: All microservices will fail
- **Action**: Immediate investigation required

### 2. PostgresHighConnections (Warning)
- **Trigger**: More than 80 active connections
- **Threshold**: 80 connections
- **Action**: Investigate connection pooling, check for connection leaks

### 3. PostgresSlowQueries (Warning)
- **Trigger**: Query efficiency drops below 50%
- **Metric**: Ratio of returned rows to fetched rows
- **Action**: Review slow query log, optimize queries, add indexes

### 4. PostgresTooManyDeadTuples (Warning)
- **Trigger**: More than 10,000 dead tuples for 10 minutes
- **Action**: Run VACUUM on affected database
- **Command**: 
  ```sql
  VACUUM ANALYZE;
  ```

## Accessing Metrics

### Direct Access
```bash
# View all PostgreSQL metrics
curl http://localhost:9187/metrics

# View specific metric
curl http://localhost:9187/metrics | grep pg_stat_database_numbackends
```

### Prometheus UI
- **Metrics Explorer**: http://localhost:9090/graph
- **Query Examples**:
  ```promql
  # Current connections to ecommerce database
  pg_stat_database_numbackends{datname="ecommerce"}
  
  # Database size in MB
  pg_database_size_bytes / 1024 / 1024
  
  # Transaction rate (commits per second)
  rate(pg_stat_database_xact_commit[5m])
  
  # Query efficiency
  rate(pg_stat_database_tup_returned[5m]) / rate(pg_stat_database_tup_fetched[5m])
  ```

### Grafana Dashboard
Import the official PostgreSQL dashboard:
- Dashboard ID: [9628](https://grafana.com/grafana/dashboards/9628) - PostgreSQL Database
- Dashboard ID: [455](https://grafana.com/grafana/dashboards/455) - PostgreSQL Overview

## Current Metrics (as of deployment)

```
Database: ecommerce
- Connections: 28
- Size: 7 MB
- Status: Healthy
- Dead Tuples: < 10,000
```

## Monitoring Best Practices

### 1. Connection Management
- Monitor active connections
- Use connection pooling (PgBouncer recommended for high traffic)
- Set max_connections appropriately

### 2. Performance
- Track query execution times
- Monitor cache hit ratios
- Watch for table bloat

### 3. Maintenance
- Schedule regular VACUUM operations
- Monitor autovacuum activity
- Track index usage

### 4. Capacity Planning
- Monitor database growth trends
- Track disk I/O metrics
- Monitor memory usage

## Troubleshooting

### postgres_exporter not connecting
```bash
# Check container logs
docker logs prometheus-metrics-postgres-exporter-1

# Verify PostgreSQL is accessible
docker exec prometheus-metrics-postgres-exporter-1 \
  wget -q -O- http://localhost:9187/metrics | grep pg_up
```

### No metrics in Prometheus
```bash
# Check if target is up
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="postgres")'

# Test scraping manually
curl http://localhost:9187/metrics
```

### High connection count
```sql
-- Check active connections
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;

-- Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;
```

### Database growing too fast
```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check dead tuples
SELECT schemaname, tablename, n_dead_tup
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

## Useful Queries

### Database Health
```promql
# Database is up
pg_up

# Current connections
sum(pg_stat_database_numbackends) by (datname)

# Connection usage percentage (assuming max_connections=100)
(sum(pg_stat_database_numbackends) / 100) * 100
```

### Performance
```promql
# Transaction rate
rate(pg_stat_database_xact_commit[5m])

# Rollback rate
rate(pg_stat_database_xact_rollback[5m])

# Cache hit ratio
sum(pg_stat_database_blks_hit) / 
(sum(pg_stat_database_blks_hit) + sum(pg_stat_database_blks_read))
```

### Table Bloat
```promql
# Dead tuples per database
sum(pg_stat_database_n_dead_tup) by (datname)

# Dead tuple ratio
pg_stat_database_n_dead_tup / pg_stat_database_n_live_tup
```

## Advanced Configuration

### Custom Queries
Create `/etc/postgres_exporter/queries.yaml` to add custom metrics:

```yaml
custom_queries:
  - query_name: "table_sizes"
    query: |
      SELECT schemaname, tablename, 
             pg_total_relation_size(schemaname||'.'||tablename) as size
      FROM pg_tables
    metrics:
      - schemaname:
          usage: "LABEL"
      - tablename:
          usage: "LABEL"
      - size:
          usage: "GAUGE"
          description: "Total table size in bytes"
```

### Environment Variables
- `DATA_SOURCE_NAME`: PostgreSQL connection string
- `PG_EXPORTER_WEB_LISTEN_ADDRESS`: Listen address (default: `:9187`)
- `PG_EXPORTER_DISABLE_DEFAULT_METRICS`: Disable default collectors
- `PG_EXPORTER_EXTEND_QUERY_PATH`: Path to custom queries file

## Resources

- [postgres_exporter GitHub](https://github.com/prometheus-community/postgres_exporter)
- [PostgreSQL Statistics Views](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [Grafana PostgreSQL Dashboards](https://grafana.com/grafana/dashboards/?search=postgresql)
- [PostgreSQL Monitoring Best Practices](https://www.postgresql.org/docs/current/monitoring.html)

## Maintenance Commands

```bash
# Restart postgres_exporter
docker-compose -f docker-compose.microservices.yml restart postgres-exporter

# View logs
docker logs prometheus-metrics-postgres-exporter-1 -f

# Test metrics endpoint
curl http://localhost:9187/metrics | grep pg_

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="postgres")'
```
