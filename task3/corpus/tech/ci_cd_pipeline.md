# CI/CD Pipeline Configuration

## Document ID: TECH-007
## Min Role: employee

Last Updated: 2025-06-01

## 1. Pipeline Architecture

AcmeCorp uses GitHub Actions for CI/CD with the following stages:

```
Push → Lint → Test → Build → Security Scan → Deploy Staging → Integration Tests → Deploy Prod
```

## 2. Pipeline Configuration File

`.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: make test

  security-scan:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.IMAGE_TAG }}
          format: sarif
          output: trivy-results.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
```

## 3. Required Checks

All PRs must pass:
- Linting (ESLint, pylint, golangci-lint)
- Unit tests (>80% coverage for new code)
- Type checking (mypy for Python, tsc for TypeScript)
- Container vulnerability scan (Trivy)
- SAST (CodeQL)

## 4. Artifact Promotion

```
dev → staging: Automatic on merge to main
staging → prod: Manual approval by release manager in GitHub Environments
```

## 5. Rollback Procedure

To rollback a production deployment:
1. Go to Actions tab → select the last good workflow run
2. Click "Re-run all jobs"
3. Verify application health in Datadog
