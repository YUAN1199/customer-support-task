# Istio Service Mesh Configuration

## Document ID: TECH-006
## Min Role: employee

Last Updated: 2025-05-01

## 1. Overview

AcmeCorp uses Istio 1.20 for service-to-service communication. Istio provides:
- Mutual TLS (mTLS) for all pod-to-pod traffic
- Traffic routing and load balancing
- Circuit breaking and retries
- Distributed tracing
- Authorization policies

## 2. Sidecar Injection

Sidecar injection is enabled by default for all namespaces with label `istio-injection: enabled`.

## 3. Authorization Policies

Default deny-all for production namespaces:

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: prod-my-service
spec: {}
```

Then explicitly allow required paths:

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-api
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/prod-api-gateway/sa/gateway"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
```

## 4. Circuit Breaking

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: user-service-cb
spec:
  host: user-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 60s
```
