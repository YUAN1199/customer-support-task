# Release Management Guide

## Document ID: TECH-013
## Min Role: employee

Last Updated: 2025-06-10

## 1. Release Cadence

AcmeCorp follows a continuous delivery model with scheduled releases:
- Hotfixes: Any time (expedited pipeline)
- Patch releases: Tuesdays and Thursdays
- Minor releases: Every 2 weeks (Wednesday deploy window)
- Major releases: Quarterly (with 2-week freeze beforehand)

## 2. Feature Flags

All new features must be behind a feature flag (LaunchDarkly) until:
- Integration tests pass in staging
- Product manager signs off
- At least 1% canary traffic validates for 24 hours without errors

## 3. Canary Deployments

Production deployments follow a progressive rollout:
```
1% → 5 min bake → 10% → 5 min bake → 50% → 5 min bake → 100%
```

Rollback is automatic if:
- Error rate increases > 0.5%
- P99 latency increases > 50%
- Health checks fail

## 4. Release Notes

Every release must include release notes posted to #releases Slack channel and the internal changelog. Format:
```
## v3.4.1 (2025-06-10)
### Added
- New export to CSV feature
### Fixed
- Memory leak in report generation (JIRA-4521)
### Security
- Updated lodash to 4.17.21 (CVE-2024-12345)
```

## 5. Rollback Decision Tree

1. Is the error rate above 1%? → Rollback now
2. Is a critical user flow broken? → Rollback now
3. Is there data corruption? → Rollback now + page on-call DBA
4. Otherwise → Assess, potentially fix-forward