# Monitoring and Alerting Guide

## Document ID: TECH-005
## Min Role: employee

Last Updated: 2025-06-01

## 1. Monitoring Stack

| Component | Tool | Access |
|-----------|------|--------|
| Metrics | Prometheus + Grafana | https://grafana.acmecorp.com |
| Logs | Elasticsearch + Kibana | https://kibana.acmecorp.com |
| Traces | Jaeger | https://jaeger.acmecorp.com |
| Alerts | PagerDuty | https://acmecorp.pagerduty.com |
| Uptime | Pingdom | https://my.pingdom.com |

## 2. Key Metrics

Every service must expose:
- Request rate (req/s)
- Error rate (5xx %)
- P50, P95, P99 latency
- CPU and memory utilization
- Database connection pool utilization

## 3. Alert Rules (Default)

```yaml
alerts:
  - name: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
    severity: P2
  - name: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
    severity: P3
  - name: ServiceDown
    expr: up == 0
    severity: P1
```

## 4. Dashboard Standards

Every service team must maintain a Grafana dashboard with:
- RED metrics (Rate, Errors, Duration)
- Resource usage (CPU, memory, disk)
- Business metrics (orders/min, users active, etc.)
- Link to service runbook

## 5. On-Call Rotation

- Each team maintains a PagerDuty schedule
- Primary on-call: 1 week rotation
- Secondary on-call: escalates after 15 min of no acknowledgment
- Handoff: Monday 10 AM with summary of previous week's incidents
