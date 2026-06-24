# Data Pipeline Architecture

## Document ID: TECH-011
## Min Role: employee

Last Updated: 2025-06-01

## 1. Overview

AcmeCorp's data pipeline processes 500 TB of event data daily through a streaming architecture built on Apache Kafka and Apache Flink.

## 2. Pipeline Stages

```
Ingest → Validate → Enrich → Transform → Aggregate → Serve
```

## 3. Technology Stack

| Stage | Technology |
|-------|-----------|
| Ingestion | Kafka Connect, Filebeat |
| Stream Processing | Apache Flink 1.18 |
| Batch Processing | Apache Spark 3.5 |
| Storage | Delta Lake on Azure Data Lake Storage Gen2 |
| Orchestration | Apache Airflow 2.8 |
| Catalog | Apache Atlas |

## 4. Kafka Configuration

- Cluster: 12 brokers, m5.2xlarge
- Topics: 200+, partitioned by tenant_id
- Retention: 7 days (default), 30 days for audit topics
- Replication factor: 3
- Min ISR: 2

## 5. Data Quality

All records must pass validation:
- Schema enforcement via Apache Avro
- Null checks on required fields
- Range checks on numeric fields
- Referential integrity against master data

Invalid records go to a dead-letter topic for manual review.

## 6. SLA

| Data Freshness | Target |
|---------------|--------|
| Real-time analytics | < 5 seconds |
| Operational dashboards | < 1 minute |
| Daily aggregates | Available by 2 AM UTC |