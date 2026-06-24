# Incident Response Plan

## Document ID: TECH-010
## Min Role: manager

Effective Date: 2025-01-01

## 1. Severity Levels

| Severity | Definition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| P1 - Critical | Complete service outage, data breach | 15 minutes | VP Engineering |
| P2 - Major | Significant feature broken, degraded performance | 30 minutes | Engineering Manager |
| P3 - Minor | Non-critical issue, workaround available | 4 hours | Team Lead |
| P4 - Cosmetic | UI glitch, typo | Next business day | None |

## 2. Response Process

### Detection
- Automated alerts from Datadog/PagerDuty
- User reports via helpdesk
- Security tooling alerts

### Response
1. Acknowledge the alert within SLA
2. Declare incident in #incidents Slack channel
3. Assign Incident Commander (IC)
4. IC opens a War Room (Zoom bridge: 555-0199)
5. IC starts a shared document for timeline

### Resolution
1. Identify root cause
2. Implement fix or rollback
3. Verify resolution with monitoring
4. Close incident and schedule postmortem

## 3. Communication Template

```
INCIDENT: [Brief title]
SEVERITY: P1/P2/P3/P4
STATUS: Investigating / Mitigating / Resolved
IMPACT: [Who/what is affected]
START: [Timestamp]
UPDATE: [Current findings]
```

## 4. Postmortem

All P1 and P2 incidents require a blameless postmortem within 5 business days. Template: https://wiki.acmecorp.com/postmortem-template
