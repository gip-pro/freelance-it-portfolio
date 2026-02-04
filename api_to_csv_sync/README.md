# API → CSV Data Sync (Python Automation)

Production-ready Python script for idempotent synchronization of REST API data into a CSV file.  
Designed for scheduled execution (cron / Windows Task Scheduler) with robust error handling and logging.

---

## 🔍 Use Case

This tool is used when API data must be regularly exported or mirrored into CSV for:
- reporting
- analytics
- backups
- integrations with legacy systems

The script guarantees **no duplicates**, **safe re-runs**, and **clear failure signals** for automation tools.

---

## ✨ Features

- REST API → CSV synchronization
- Idempotent updates based on unique ID
- Automatic retries with backoff on network errors
- Strict API response validation
- CLI interface for automation pipelines
- Structured logging to file and stdout
- Meaningful exit codes for cron / schedulers
- Optional dry-run mode (no file writes)
- Optional record limit for testing

---

## ⚙️ Requirements

- Python 3.9+
- requests

Install dependencies:
```bash
pip install requests
