# API Gateway Configuration Guide

## Document ID: TECH-003
## Min Role: employee

Last Updated: 2025-06-10

## 1. Architecture

AcmeCorp uses Kong API Gateway (v3.4) deployed on Kubernetes for all external API traffic. Internal service-to-service communication uses a service mesh (Istio).

## 2. Route Configuration

Routes are defined declaratively in `kong/` directories within each service repository:

```yaml
services:
  - name: user-service
    url: http://user-service.prod-user-service.svc.cluster.local:8080
    routes:
      - name: user-api
        paths:
          - /api/v1/users
        methods:
          - GET
          - POST
        strip_path: false
```

## 3. Authentication

All external API endpoints require authentication:
- OAuth 2.0 with JWT (via Okta)
- API keys for service-to-service calls (managed in Kong)
- mTLS for Tier 3+ data endpoints

## 4. Rate Limiting

| Tier | Rate Limit | Burst |
|------|-----------|-------|
| Free tier partners | 100 req/min | 20 |
| Premium partners | 1000 req/min | 100 |
| Internal services | 5000 req/min | 500 |

## 5. Plugins

Standard plugin stack for all routes:
- `rate-limiting` — Enforce rate limits
- `request-transformer` — Normalize headers
- `cors` — Allow configured origins
- `prometheus` — Export metrics
- `zipkin` — Distributed tracing via Jaeger

## 6. Monitoring

Kong metrics are exported to Prometheus and visualized in Grafana. Alert thresholds:
- 5xx error rate > 1% triggers P2 alert
- P99 latency > 2000ms triggers P3 alert
- Certificate expiry < 30 days triggers P3 alert
