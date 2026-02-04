# API to CSV Sync — Production-Ready Data Synchronization Script

A robust, cron-friendly Python script that keeps your CSV data perfectly synchronized with a REST API.
Designed for reliability, idempotency, and real-world production workloads.

This repository is preconfigured and demonstrated using the public test API:
https://jsonplaceholder.typicode.com/posts

## Key Features
- Idempotent sync using a unique record ID
- Safe for scheduled execution (cron / task scheduler)
- Supports dry-run mode for testing and validation
- Optional limit for controlled or partial syncs
- Automatic update of changed records
- Automatic insertion of new records
- Built-in retry logic and network error handling
- Clear exit codes for monitoring and automation
- Detailed logging to file and stdout

## Typical Use Cases
- Periodic API → CSV data exports
- Lightweight ETL pipelines
- Monitoring or reporting datasets
- Safe data sync jobs in CI/CD or cron environments

## Usage

Basic run (JSONPlaceholder demo API):

python api_to_csv_sync.py \
  --api-url https://jsonplaceholder.typicode.com/posts \
  --csv-path data.csv

Dry-run (no file changes):

python api_to_csv_sync.py \
  --api-url https://jsonplaceholder.typicode.com/posts \
  --csv-path data.csv \
  --dry-run

Limit processed records:

python api_to_csv_sync.py \
  --api-url https://jsonplaceholder.typicode.com/posts \
  --csv-path data.csv \
  --limit 50

## Cron Example

Run every 10 minutes:

*/10 * * * * /usr/bin/python3 /path/api_to_csv_sync.py --api-url https://jsonplaceholder.typicode.com/posts --csv-path /path/data.csv

## Exit Codes
- 0 — Success
- 1 — General execution error
- 2 — API communication error
- 3 — Data validation error
- 4 — File read/write error

## Requirements
- Python 3.9+
- requests

## Logging
All operations are logged to `sync.log`, making the script easy to audit and monitor in production.

---

This script is intentionally simple, predictable, and safe — ideal for long-running systems where data consistency matters.