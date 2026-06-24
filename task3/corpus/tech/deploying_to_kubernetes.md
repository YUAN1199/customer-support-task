# Deploying Applications to Kubernetes

## Document ID: TECH-001
## Min Role: employee

Last Updated: 2025-06-01

## 1. Overview

AcmeCorp's production workloads run on a managed Kubernetes cluster (AKS in Azure). This guide covers the standard deployment process for new applications.

## 2. Prerequisites

- Access to the `acmecorp-prod` AKS cluster (request via Jira ticket to DevOps)
- `kubectl` installed and configured (see TECH-002)
- `helm` v3.12+ installed
- Docker image pushed to `acmecorp.azurecr.io`

## 3. Namespace Convention

| Environment | Namespace | Example |
|-------------|-----------|---------|
| Development | `dev-{team}` | dev-platform |
| Staging | `staging-{team}` | staging-platform |
| Production | `prod-{service}` | prod-api-gateway |

## 4. Deployment Manifest Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
  namespace: prod-my-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-service
  template:
    metadata:
      labels:
        app: my-service
    spec:
      containers:
      - name: app
        image: acmecorp.azurecr.io/my-service:latest
        ports:
        - containerPort: 8080
```

## 5. Resource Limits

All containers must specify resource limits:
- CPU: Request 100m, Limit 500m (default)
- Memory: Request 256Mi, Limit 1Gi (default)
- Higher limits require architecture review approval

## 6. Health Checks

- Liveness probe: `/healthz` endpoint, initial delay 30s, period 10s
- Readiness probe: `/ready` endpoint, initial delay 10s, period 5s

## 7. Secrets Management

Never store secrets in deployment manifests. Use Azure Key Vault with the Secrets Store CSI driver. Reference secrets as:

```yaml
volumeMounts:
- name: secrets
  mountPath: /mnt/secrets
  readOnly: true
```
