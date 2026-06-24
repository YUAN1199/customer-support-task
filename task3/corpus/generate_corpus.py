"""Generate 30+ corpus documents for the Enterprise Knowledge Assistant."""
import os

DOCS = {}

DOCS["policies/password_policy.md"] = """# Password Policy

## Document ID: POL-003
## Min Role: employee

Effective Date: 2025-01-01

## 1. Purpose

This policy defines password requirements for all AcmeCorp systems and applications.

## 2. Password Requirements

- Minimum length: 14 characters
- Must contain at least one uppercase letter, one lowercase letter, one number, and one special character
- Must not contain your username, real name, or company name
- Must not reuse any of your last 10 passwords
- Passwords expire every 90 days

## 3. Multi-Factor Authentication

MFA is required for:
- Remote access (VPN)
- Email access from outside the corporate network
- Administrative access to production systems
- Access to Tier 3 and Tier 4 data

Use the AcmeCorp Authenticator app or a FIDO2 hardware key. SMS-based MFA is being phased out.

## 4. Password Managers

- Use of the company-approved password manager (KeePassXC) is strongly recommended.
- Store your master password securely; do not write it down.
- Never store passwords in plaintext files, sticky notes, or browser password managers for Tier 3+ systems.

## 5. Incident Response

If you suspect your password has been compromised:
1. Change it immediately via the Self-Service Portal
2. Report the incident to soc@acmecorp.com
3. Review recent account activity for unauthorized access
"""

DOCS["policies/remote_work.md"] = """# Remote Work Policy

## Document ID: POL-004
## Min Role: employee

Effective Date: 2025-03-01

## 1. Eligibility

All full-time employees may work remotely up to 3 days per week with manager approval. Interns must work on-site for the first 3 months before becoming eligible for remote work.

## 2. Workspace Requirements

- Dedicated workspace free from distractions
- Ergonomically appropriate desk and chair (reimbursement up to $500 available)
- Reliable internet connection (minimum 25 Mbps download / 5 Mbps upload)

## 3. Security Requirements

- VPN must be active at all times when accessing internal resources
- Use only AcmeCorp-issued devices for work
- Lock your screen when away from your workstation
- Do not print Tier 3+ documents at home

## 4. Communication

- Be available on Slack during core hours (10 AM - 4 PM local time)
- Camera-on is expected for client-facing meetings
- Respond to messages within 30 minutes during core hours

## 5. Equipment

- Laptops: Standard issue is a Dell Latitude 7450 with 32 GB RAM
- Monitors: One 27" 4K monitor provided for home office
- Headset: Jabra Evolve2 65 provided
- Report equipment issues to IT within 24 hours
"""

DOCS["policies/vacation_leave.md"] = """# Vacation & Leave Policy

## Document ID: POL-005
## Min Role: intern

Effective Date: 2025-01-01

## 1. Vacation Days

| Employment Tier | Annual Vacation Days |
|----------------|---------------------|
| Intern | 5 days |
| Employee (0-3 years) | 15 days |
| Employee (3-7 years) | 20 days |
| Employee (7+ years) | 25 days |
| Manager | 25 days |
| Admin | 30 days |

Vacation days accrue monthly and may carry over up to 5 unused days per year.

## 2. Sick Leave

All employees receive 10 sick days per year. A doctor's note is required for absences of 3+ consecutive days.

## 3. Parental Leave

- Birthing parents: 16 weeks fully paid
- Non-birthing parents: 8 weeks fully paid
- Adoption: 12 weeks fully paid
- Must have been employed for at least 12 months to qualify

## 4. Request Process

Submit leave requests through Workday at least:
- 2 weeks in advance for vacation of 3+ days
- 1 week in advance for 1-2 days
- As soon as possible for sick leave

## 5. Public Holidays

AcmeCorp observes 11 public holidays per year. See the company calendar for exact dates.
"""

DOCS["policies/expense_policy.md"] = """# Expense Reimbursement Policy

## Document ID: POL-006
## Min Role: employee

Effective Date: 2025-01-01

## 1. General Rules

- All expenses must be business-related and reasonable in amount.
- Submit receipts within 30 days via Concur.
- Expenses over $75 require an itemized receipt.
- Expenses over $500 require pre-approval from your manager.

## 2. Travel

- Flights: Economy class for domestic; Premium Economy for international over 6 hours
- Hotels: Up to $250/night (domestic), $400/night (international)
- Meals: Up to $75/day (domestic), $100/day (international)
- Rental cars: Midsize or equivalent; always decline the rental company's insurance (corporate card covers it)

## 3. Client Entertainment

- Pre-approval required for expenses over $200
- Alcohol is reimbursable up to 2 drinks per person
- Entertainment expenses must include client name(s) and business purpose

## 4. Home Office

- One-time reimbursement up to $500 for desk/chair
- Monthly stipend of $75 for internet (submit quarterly)
- Office supplies reimbursable up to $50/month

## 5. Non-Reimbursable

- Personal meals during regular work hours
- Traffic tickets, parking fines
- Airline upgrades (unless using personal points)
- Gym fees or personal entertainment
- Gifts over $25 (requires separate gift approval process)
"""

DOCS["policies/code_of_conduct.md"] = """# Code of Conduct

## Document ID: POL-007
## Min Role: intern

Effective Date: 2025-01-01

## 1. Our Commitment

AcmeCorp is committed to providing a safe, inclusive, and respectful workplace for all employees, contractors, and visitors.

## 2. Expected Behavior

- Treat all individuals with respect and dignity
- Communicate professionally in all channels (email, Slack, meetings)
- Respect confidentiality of business and personal information
- Comply with all applicable laws and regulations
- Report unethical behavior promptly

## 3. Prohibited Conduct

- Harassment, discrimination, or bullying of any kind
- Retaliation against those who report concerns in good faith
- Use of company resources for personal financial gain
- Conflicts of interest without disclosure
- Possession of weapons on company property

## 4. Reporting

Report concerns to:
- Your manager (if comfortable)
- HR Business Partner: hr@acmecorp.com
- Anonymous Ethics Hotline: 1-800-555-ETHICS

All reports are investigated promptly and confidentially to the extent possible. Retaliation is strictly prohibited.

## 5. Disciplinary Actions

Violations may result in:
- Verbal or written warning
- Mandatory training
- Suspension
- Termination of employment
- Legal action
"""

DOCS["policies/onboarding_checklist.md"] = """# New Hire Onboarding Checklist

## Document ID: POL-008
## Min Role: intern

Effective Date: 2025-03-01

## Week 1: Before Start Date

- [ ] HR sends offer letter and background check authorization
- [ ] IT prepares laptop (Dell Latitude 7450), monitors, and peripherals
- [ ] Manager assigns onboarding buddy
- [ ] Accounts created: Google Workspace, Slack, GitHub Enterprise, Jira

## Week 1: Day 1

- [ ] Badge photo and building access card (visit Security Office, Building A, Room 101)
- [ ] Laptop pickup and initial login
- [ ] Complete I-9 verification with HR
- [ ] Benefits enrollment overview (must complete within 30 days)
- [ ] Tour of office facilities

## Week 1: Days 2-5

- [ ] Security awareness training (mandatory, 2 hours)
- [ ] Code of Conduct acknowledgment
- [ ] Meet the team (schedule 15-min 1:1s)
- [ ] Set up development environment (see TECH-001)
- [ ] Review team's documentation in Confluence

## Month 1

- [ ] Complete role-specific training plan with manager
- [ ] Attend company all-hands (first Thursday of month)
- [ ] Set up 401(k) contributions through Fidelity
- [ ] 30-day check-in with manager and HR

## Month 3

- [ ] 90-day probation review
- [ ] Goal setting for remainder of year
- [ ] Interns: project presentation to team
"""

DOCS["policies/performance_review.md"] = """# Performance Review Policy

## Document ID: POL-009
## Min Role: employee

Effective Date: 2025-01-01

## 1. Review Cycle

AcmeCorp operates on a semi-annual performance review cycle:
- Mid-Year Review: July 1-15
- Year-End Review: January 5-20

## 2. Review Components

Each review consists of:
- Self-assessment (submitted 1 week before the review meeting)
- Peer feedback (minimum 3 peers)
- Manager assessment
- Goal progress tracking

## 3. Rating Scale

| Rating | Description | Impact |
|--------|-------------|--------|
| 5 - Exceptional | Consistently exceeds expectations; role model | Top bonus tier, accelerated promotion |
| 4 - Exceeds | Frequently exceeds expectations | Above-target bonus |
| 3 - Meets | Consistently meets expectations | Target bonus |
| 2 - Needs Improvement | Occasionally below expectations | Reduced bonus, performance improvement plan |
| 1 - Unsatisfactory | Consistently below expectations | No bonus, PIP mandatory |

## 4. Compensation

- Merit increases are determined during the Year-End Review cycle.
- Promotions are considered at either review cycle.
- Bonus pool is allocated based on company performance and individual rating.

## 5. Performance Improvement Plan (PIP)

Employees receiving a "Needs Improvement" or "Unsatisfactory" rating will be placed on a 90-day PIP with specific, measurable goals. Failure to meet PIP goals may result in termination.
"""

DOCS["tech/deploying_to_kubernetes.md"] = """# Deploying Applications to Kubernetes

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
"""

DOCS["tech/development_environment_setup.md"] = """# Development Environment Setup

## Document ID: TECH-002
## Min Role: intern

Last Updated: 2025-05-15

## 1. Supported Operating Systems

- macOS 13+ (Ventura or later)
- Ubuntu 22.04 LTS or 24.04 LTS
- Windows 11 with WSL2 (Ubuntu 22.04)

## 2. Required Tools

### Core Tools
- Git 2.40+
- Docker Desktop 4.20+
- Python 3.11+ (via pyenv recommended)
- Node.js 20 LTS (via nvm)
- Go 1.21+

### CLI Tools
- `kubectl` — Follow official Kubernetes install guide
- `helm` v3.12+ — `brew install helm` or `choco install kubernetes-helm`
- `azure-cli` — `brew install azure-cli` or `winget install Microsoft.AzureCLI`
- `terraform` 1.6+ — `brew install terraform`

### IDE
- VS Code (recommended) with extensions: Python, Go, Kubernetes, Docker, Prettier
- IntelliJ IDEA Ultimate for Java/Kotlin projects (license provided)

## 3. Repository Access

- GitHub Enterprise: https://github.acmecorp.com
- Authenticate via SAML SSO (Okta)
- Clone repos via SSH: `git clone git@github.acmecorp.com:team/repo.git`

## 4. Local Services

Use Docker Compose for local development:
```bash
docker compose -f dev/docker-compose.yml up -d
```
This starts PostgreSQL 15, Redis 7, and LocalStack (AWS emulator).

## 5. Environment Variables

Copy `.env.example` to `.env` and fill in required values. Never commit `.env` files.
Use `direnv` or `dotenv` for automatic loading.
"""

DOCS["tech/api_gateway_configuration.md"] = """# API Gateway Configuration Guide

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
"""

DOCS["tech/incident_response.md"] = """# Incident Response Plan

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
"""

DOCS["tech/database_operations.md"] = """# Database Operations Guide

## Document ID: TECH-004
## Min Role: employee

Last Updated: 2025-05-20

## 1. Supported Databases

- PostgreSQL 15 (primary relational database)
- Redis 7 (caching, session store)
- MongoDB 7 (document store for unstructured data)
- Elasticsearch 8 (search and analytics)

## 2. PostgreSQL Connection Strings

```
# Development
postgresql://user:pass@localhost:5432/acmecorp_dev

# Staging
postgresql://app_user@acmecorp-staging.postgres.database.azure.com:5432/acmecorp_staging?sslmode=require

# Production — Credentials in Azure Key Vault only
```

## 3. Backup Policy

| Database | Full Backup | Point-in-Time Recovery | Retention |
|----------|------------|----------------------|-----------|
| PostgreSQL Prod | Daily | Yes (WAL archiving) | 30 days |
| PostgreSQL Non-Prod | Weekly | No | 7 days |
| MongoDB | Daily | No | 14 days |
| Redis | Hourly RDB snapshots | No | 2 days |

## 4. Migration Process

All schema changes must go through:
1. Write migration script (SQL or using Alembic for Python)
2. Test against a staging clone
3. Review by Database Team (PR in `db-migrations` repo)
4. Schedule maintenance window if downtime required
5. Execute via CI/CD pipeline (`apply-migrations` job)
6. Verify application health after migration

## 5. Performance Guidelines

- All tables must have primary keys
- Index foreign key columns
- Use `EXPLAIN ANALYZE` before deploying queries touching >10K rows
- Connection pooling: max 100 connections per service instance
- Query timeout: 30 seconds (production default)
"""

DOCS["tech/monitoring_and_alerting.md"] = """# Monitoring and Alerting Guide

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
"""

DOCS["tech/service_mesh_istio.md"] = """# Istio Service Mesh Configuration

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
"""

DOCS["onboarding/welcome_to_acmecorp.md"] = """# Welcome to AcmeCorp!

## Document ID: ONB-001
## Min Role: intern

## About AcmeCorp

Founded in 2010, AcmeCorp is a leader in enterprise SaaS solutions, serving over 5,000 customers across 40 countries. Our mission is to simplify complex business workflows through intelligent automation.

## Our Values

- **Customer First** — Every decision starts with the customer's needs.
- **Innovation with Integrity** — We push boundaries, but we do it ethically.
- **Collaborate Openly** — Best ideas win, regardless of where they come from.
- **Continuous Learning** — We invest in your growth.
- **Work-Life Harmony** — Sustainable pace > heroic crunch.

## Office Locations

| Location | Address | Capacity |
|----------|---------|----------|
| Headquarters | 100 Innovation Drive, San Francisco, CA 94105 | 800 |
| New York | 200 Park Avenue, 45th Floor, NY 10166 | 300 |
| London | 30 St Mary Axe, London EC3A 8BF | 200 |
| Bangalore | WeWork, Prestige Tech Park, Bangalore 560103 | 400 |
| Tokyo | Shiodome City Center, Minato-ku, Tokyo 105-7100 | 100 |

## Key Contacts

- HR: hr@acmecorp.com
- IT Help Desk: helpdesk@acmecorp.com, ext. 1234
- Facilities: facilities@acmecorp.com
- Security Operations: soc@acmecorp.com, ext. 5555
"""

DOCS["onboarding/benefits_overview.md"] = """# Employee Benefits Overview

## Document ID: ONB-002
## Min Role: intern

## Health Insurance

- Medical: Aetna PPO with $500 deductible. AcmeCorp covers 90% of premium.
- Dental: Delta Dental PPO with $50 deductible. 100% preventive coverage.
- Vision: VSP with $10 copay for exams. $150 annual frame allowance.

## Retirement

- 401(k) through Fidelity with 4% company match (100% vested immediately)
- Roth 401(k) option available
- Access to financial advisors at no cost

## Equity

- Stock options granted at hire (4-year vest: 25% after 1 year, monthly thereafter)
- Annual refresh grants based on performance

## Learning & Development

- $2,000 annual education stipend (conferences, courses, books)
- LinkedIn Learning and O'Reilly subscriptions provided
- Internal mentorship program

## Wellness

- $100 monthly wellness reimbursement (gym, yoga, meditation apps)
- Employee Assistance Program (EAP): free counseling, legal, and financial advice
- Quarterly wellness days (company-wide day off)

## Commuter Benefits

- Pre-tax commuter benefits up to $300/month
- Secure bike storage and showers at all offices
- EV charging stations at HQ and NY offices
"""

DOCS["onboarding/company_tools.md"] = """# Company Tools & Software

## Document ID: ONB-003
## Min Role: intern

## Communication

| Tool | Purpose | URL |
|------|---------|-----|
| Google Workspace | Email, Calendar, Docs, Drive | https://mail.acmecorp.com |
| Slack | Team chat | https://acmecorp.slack.com |
| Zoom | Video conferencing | https://acmecorp.zoom.us |
| Confluence | Documentation wiki | https://wiki.acmecorp.com |

## Development

| Tool | Purpose | URL |
|------|---------|-----|
| GitHub Enterprise | Source code | https://github.acmecorp.com |
| Jira | Issue tracking, agile planning | https://acmecorp.atlassian.net |
| Jenkins | CI/CD | https://ci.acmecorp.com |
| Artifactory | Package registry | https://artifact.acmecorp.com |
| SonarQube | Code quality analysis | https://sonar.acmecorp.com |

## Operations

| Tool | Purpose | URL |
|------|---------|-----|
| PagerDuty | On-call & incident management | https://acmecorp.pagerduty.com |
| Datadog | Infrastructure monitoring | https://app.datadoghq.com |
| Terraform Cloud | Infrastructure as Code | https://app.terraform.io |

## HR & Admin

| Tool | Purpose | URL |
|------|---------|-----|
| Workday | HR, payroll, time off | https://acmecorp.workday.com |
| Concur | Expenses | https://acmecorp.concur.com |
| Fidelity | 401(k) benefits | https://www.fidelity.com |
| Okta | Single Sign-On | https://acmecorp.okta.com |
"""

DOCS["onboarding/team_structure.md"] = """# Engineering Team Structure

## Document ID: ONB-004
## Min Role: intern

## Engineering Leadership

| Role | Name | Contact |
|------|------|---------|
| CTO | Dr. Sarah Chen | sarah.chen@acmecorp.com |
| VP Engineering | Marcus Johnson | marcus.johnson@acmecorp.com |
| Director, Platform | Aisha Patel | aisha.patel@acmecorp.com |
| Director, Product Engineering | David Kim | david.kim@acmecorp.com |

## Teams

### Platform Engineering (Director: Aisha Patel)
- **Infrastructure**: Kubernetes, networking, cloud (Azure)
- **Developer Experience**: CI/CD, local dev tooling, documentation
- **Security Engineering**: AppSec, compliance, incident response
- **Data Platform**: Databases, data pipeline, ML infrastructure

### Product Engineering (Director: David Kim)
- **Core Product**: Main application development
- **Integrations**: Third-party API integrations
- **Mobile**: iOS and Android apps
- **Analytics**: Customer-facing analytics and reporting

## Agile Practices

- 2-week sprints (Wednesday to Tuesday)
- Standups: 9:30 AM daily on Slack (#team-* channels)
- Sprint planning: Wednesday 10 AM
- Retrospectives: Tuesday 3 PM
- Demos: Tuesday 4 PM (all-hands welcome)

## Career Ladder

| Level | Title | Experience |
|-------|-------|-----------|
| L1 | Associate Engineer | 0-2 years |
| L2 | Engineer | 2-5 years |
| L3 | Senior Engineer | 5-8 years |
| L4 | Staff Engineer | 8-12 years |
| L5 | Principal Engineer | 12+ years |
| M1 | Engineering Manager | — |
| M2 | Director | — |
"""

DOCS["onboarding/security_training.md"] = """# Security Awareness Training

## Document ID: ONB-005
## Min Role: intern

## Required Training

All new hires must complete Security Awareness Training within the first week. This takes approximately 2 hours and covers:
- Phishing and social engineering awareness
- Password best practices
- Data classification and handling
- Physical security
- Incident reporting procedures

## Phishing Awareness

- Check the sender's email address carefully
- Hover over links before clicking
- Be suspicious of urgent language ("Your account will be deleted!")
- Never enter credentials after clicking an email link — navigate directly
- Report suspected phishing to phishing@acmecorp.com

## Physical Security

- Always wear your badge visibly in office
- Challenge tailgaters — "Can I help you find your badge?"
- Lock your screen when away: Windows Key + L (Windows) or Control + Command + Q (Mac)
- Never leave laptops unattended in public spaces
- Use privacy screens when working in public (airports, cafes)

## Clean Desk Policy

- Lock sensitive documents in drawers overnight
- Whiteboards with confidential information must be erased after meetings
- Shred documents containing PII or trade secrets
- Do not write passwords on sticky notes

## Data Classification Quick Reference

| Data Type | Examples | Storage | Sharing |
|-----------|----------|---------|---------|
| Public | Press releases, job postings | Anywhere | Unrestricted |
| Internal | Team docs, roadmaps | Cloud services | Internal only |
| Confidential | PII, financial data | Encrypted stores | Need-to-know |
| Restricted | Trade secrets, M&A | Vaulted, MFA | Explicit auth only |
"""

DOCS["tech/ci_cd_pipeline.md"] = """# CI/CD Pipeline Configuration

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
"""

DOCS["tech/logging_standards.md"] = """# Logging Standards

## Document ID: TECH-008
## Min Role: employee

Last Updated: 2025-04-15

## 1. Log Format

All application logs must be structured JSON:

```json
{
  "timestamp": "2025-06-24T12:00:00Z",
  "level": "INFO",
  "service": "user-service",
  "trace_id": "abc123def456",
  "span_id": "span789",
  "message": "User login successful",
  "user_id": "usr_12345",
  "duration_ms": 45
}
```

## 2. Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info (dev only by default) |
| INFO | Normal operations, business events |
| WARN | Potential issues, degraded operation |
| ERROR | Operation failures, exceptions |
| FATAL | Service cannot continue, requires restart |

## 3. What to Log

- Service start/stop events
- Request/response (sanitized, no PII)
- Authentication events (success/failure, never log passwords)
- Database query times (>100ms should be WARN)
- External API call results
- Errors with stack traces

## 4. What NOT to Log

- Passwords, tokens, API keys (use `***REDACTED***`)
- Full credit card numbers (log last 4 only if needed)
- Social security numbers
- Full PII (emails may be partially logged: `j***@acmecorp.com`)
- Health information (HIPAA-protected data)

## 5. Retention

| Environment | Retention |
|-------------|-----------|
| Production | 30 days in Elasticsearch, 1 year in cold storage |
| Staging | 7 days |
| Development | 3 days |
"""

DOCS["policies/privacy_policy.md"] = """# Employee Privacy Policy

## Document ID: POL-010
## Min Role: employee

Effective Date: 2025-01-01

## 1. Scope

This policy describes how AcmeCorp collects, uses, and protects employee personal information.

## 2. Information We Collect

- Contact information (name, address, phone, email)
- Employment records (title, salary, performance reviews)
- Benefits enrollment information
- Time and attendance records
- IT usage logs (email, web browsing, application access)

## 3. How We Use Information

- Administering payroll and benefits
- Performance management
- Security monitoring and incident response
- Legal compliance (tax reporting, employment verification)
- Workforce planning and analytics (aggregated, anonymized)

## 4. Monitoring

AcmeCorp monitors:
- Corporate email (content and metadata)
- Web browsing activity through corporate network
- Access to internal systems and data
- Building access logs

Monitoring is for security and compliance purposes. Employees have no expectation of privacy when using AcmeCorp IT resources.

## 5. Data Subject Rights

Under applicable privacy laws (GDPR, CCPA), employees may:
- Request access to their personal data
- Request correction of inaccurate data
- Request deletion of data (subject to legal retention requirements)
- Object to certain processing activities

Submit requests to privacy@acmecorp.com. Response within 30 days.

## 6. Contact

- Data Protection Officer: privacy@acmecorp.com
- Legal Department: legal@acmecorp.com
"""

DOCS["tech/api_design_guide.md"] = """# API Design Guidelines

## Document ID: TECH-009
## Min Role: employee

Last Updated: 2025-05-01

## 1. REST API Conventions

### URL Structure
```
https://api.acmecorp.com/v1/{resource}
https://api.acmecorp.com/v1/{resource}/{id}
https://api.acmecorp.com/v1/{resource}/{id}/{sub-resource}
```

### HTTP Methods
| Method | Action | Idempotent |
|--------|--------|-----------|
| GET | Retrieve | Yes |
| POST | Create | No |
| PUT | Full replace | Yes |
| PATCH | Partial update | No |
| DELETE | Remove | Yes |

## 2. Response Format

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "page": 1,
    "page_size": 20,
    "total_count": 150
  },
  "errors": []
}
```

## 3. Error Responses

```json
{
  "data": null,
  "meta": { "request_id": "req_abc123" },
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "email field is required",
      "field": "email"
    }
  ]
}
```

Standard error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`, `RATE_LIMITED`, `INTERNAL_ERROR`.

## 4. Pagination

Use cursor-based pagination for large datasets:
```
GET /v1/users?cursor=eyJpZCI6MTIzfQ==&limit=50
```

Response includes `next_cursor` and `has_more` fields.

## 5. Versioning

- URL-based versioning: `/v1/`, `/v2/`
- Deprecation: announce 6 months in advance via `Sunset` HTTP header
- Maintain backward compatibility within a major version

## 6. Rate Limiting Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1688000000
Retry-After: 60
```
"""

def get_all_docs():
    """Return all corpus documents as (path, content) tuples."""
    return [(path, content) for path, content in DOCS.items()]


def write_corpus(base_dir: str = "corpus"):
    """Write all documents to disk."""
    for rel_path, content in DOCS.items():
        full_path = os.path.join(base_dir, rel_path)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
    print(f"Written {len(DOCS)} documents to {base_dir}/")

if __name__ == "__main__":
    write_corpus()