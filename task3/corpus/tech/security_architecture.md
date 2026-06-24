# Security Architecture Overview

## Document ID: TECH-012
## Min Role: employee

Last Updated: 2025-06-15

## 1. Security Principles

AcmeCorp follows defense-in-depth with these core principles:
- Zero Trust: Never trust, always verify
- Least Privilege: Grant minimum access needed
- Secure by Default: All services start locked down
- Assume Breach: Design for containment

## 2. Network Architecture

```
Internet → WAF (Cloudflare) → CDN → Load Balancer → API Gateway → Microservices
                                                    ↘ Auth (Okta)
                                                    ↘ DDoS Protection (Azure)
```

## 3. Identity & Access

- SSO via Okta with SAML 2.0
- MFA enforced for all human users
- Service accounts use managed identities (Azure AD)
- Access reviews: quarterly for Tier 3+, annual for all

## 4. Encryption Standards

| Context | Algorithm | Key Size |
|---------|-----------|----------|
| Data at rest | AES-256-GCM | 256-bit |
| Data in transit | TLS 1.3 | — |
| Password hashing | bcrypt | cost=12 |
| API tokens | HMAC-SHA256 | 256-bit |

## 5. Vulnerability Management

- SAST scans on every PR (CodeQL)
- DAST scans weekly on staging (OWASP ZAP)
- Container scanning on every build (Trivy)
- Dependency scanning daily (Dependabot, Snyk)
- Penetration testing: quarterly by external firm

## 6. Compliance

AcmeCorp maintains:
- SOC 2 Type II (annual audit)
- ISO 27001 certified
- GDPR compliant (EU DPO appointed)
- HIPAA compliant for healthcare products