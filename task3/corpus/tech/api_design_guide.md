# API Design Guidelines

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
