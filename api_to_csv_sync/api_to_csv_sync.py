import argparse
import csv
import logging
import os
import sys
import time
from typing import Dict, List

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_API_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_IO_ERROR = 4

REQUEST_TIMEOUT = 15
MAX_RETRIES = 5
RETRY_BACKOFF = 5

ID_FIELD = "id"

LOG_PATH = "sync.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="API to CSV sync")
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Run without writing CSV")
    parser.add_argument("--limit", type=int, help="Limit number of processed API records")
    return parser.parse_args()


def fetch_api_data(api_url: str) -> List[Dict]:
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(api_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("API response must be a list")
            return data
        except Timeout as e:
            logger.error(f"Timeout error: {e}")
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            break
        except ValueError as e:
            logger.error(f"Invalid JSON structure: {e}")
            sys.exit(EXIT_VALIDATION_ERROR)

        retries += 1
        logger.info(f"Retry {retries}/{MAX_RETRIES}")
        time.sleep(RETRY_BACKOFF)

    sys.exit(EXIT_API_ERROR)


def validate_item(item: Dict) -> bool:
    return isinstance(item, dict) and ID_FIELD in item


def load_csv(path: str) -> Dict[str, Dict]:
    if not os.path.exists(path):
        return {}

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return {row[ID_FIELD]: row for row in reader}
    except Exception as e:
        logger.error(f"CSV read error: {e}")
        sys.exit(EXIT_IO_ERROR)


def save_csv(path: str, rows: Dict[str, Dict]):
    if not rows:
        return

    fieldnames = list(next(iter(rows.values())).keys())

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows.values())
    except Exception as e:
        logger.error(f"CSV write error: {e}")
        sys.exit(EXIT_IO_ERROR)


def sync(api_url: str, csv_path: str, dry_run: bool, limit: int | None):
    logger.info("Sync started")

    api_items = fetch_api_data(api_url)
    if limit:
        api_items = api_items[:limit]

    csv_rows = load_csv(csv_path)

    added = 0
    updated = 0

    for item in api_items:
        if not validate_item(item):
            logger.error(f"Invalid item structure: {item}")
            sys.exit(EXIT_VALIDATION_ERROR)

        item_id = str(item[ID_FIELD])
        normalized = {k: str(v) for k, v in item.items()}

        if item_id in csv_rows:
            if csv_rows[item_id] != normalized:
                csv_rows[item_id] = normalized
                updated += 1
        else:
            csv_rows[item_id] = normalized
            added += 1

    if dry_run:
        logger.info(
            f"Dry-run mode. Would add: {added}, update: {updated}, total result: {len(csv_rows)}"
        )
        sys.exit(EXIT_OK)

    save_csv(csv_path, csv_rows)

    logger.info(
        f"Sync finished successfully. Total: {len(csv_rows)}, added: {added}, updated: {updated}"
    )
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    args = parse_args()
    sync(args.api_url, args.csv_path, args.dry_run, args.limit)