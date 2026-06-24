# Logging Standards

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
