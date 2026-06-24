# Password Policy

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
