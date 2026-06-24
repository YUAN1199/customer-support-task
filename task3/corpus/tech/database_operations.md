# Database Operations Guide

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
