import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Dict

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_API_ERROR = 2
EXIT_IO_ERROR = 3
EXIT_RATE_LIMIT = 4

LOG_PATH = "downloader.log"

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
    parser = argparse.ArgumentParser(description="API file downloader")
    parser.add_argument("--api-url", required=True, help="API endpoint with file metadata")
    parser.add_argument("--output-dir", default="downloads", help="Base directory for files")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=5, help="Max retry attempts")
    parser.add_argument("--retry-backoff", type=int, default=5, help="Backoff between retries in seconds")
    parser.add_argument("--rate-limit-backoff", type=int, default=30, help="Backoff for HTTP 429 in seconds")
    return parser.parse_args()


def fetch_metadata(api_url: str, timeout: int, max_retries: int, retry_backoff: int, rl_backoff: int) -> List[Dict]:
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(api_url, timeout=timeout)
            if response.status_code == 429:
                logger.warning(f"Rate limit hit. Sleeping {rl_backoff}s")
                time.sleep(rl_backoff)
                continue

            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("API response must be a list")
            return data

        except Timeout as e:
            logger.error(f"Timeout: {e}")
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            break
        except ValueError as e:
            logger.error(f"Invalid API format: {e}")
            sys.exit(EXIT_API_ERROR)

        retries += 1
        time.sleep(retry_backoff)

    sys.exit(EXIT_API_ERROR)


def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error(f"Directory creation failed: {e}")
        sys.exit(EXIT_IO_ERROR)


def download_file(url: str, target_path: str, timeout: int, max_retries: int, retry_backoff: int, rl_backoff: int):
    if os.path.exists(target_path):
        return False

    tmp_path = target_path + ".tmp"
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 429:
                logger.warning(f"Rate limit while downloading. Sleeping {rl_backoff}s")
                time.sleep(rl_backoff)
                continue

            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            os.replace(tmp_path, target_path)
            return True

        except Timeout as e:
            logger.error(f"Timeout downloading {url}: {e}")
        except ConnectionError as e:
            logger.error(f"Connection error downloading {url}: {e}")
        except HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e}")
            break
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        retries += 1
        time.sleep(retry_backoff)

    return False


def process_files(args):
    logger.info("Download process started")

    items = fetch_metadata(
        args.api_url,
        args.timeout,
        args.max_retries,
        args.retry_backoff,
        args.rate_limit_backoff
    )

    downloaded = 0
    skipped = 0

    for item in items:
        if not all(k in item for k in ("id", "file_url", "date", "filename")):
            logger.error(f"Invalid item structure: {item}")
            continue

        try:
            file_date = datetime.fromisoformat(item["date"])
        except Exception:
            logger.error(f"Invalid date format: {item}")
            continue

        dir_path = os.path.join(
            args.output_dir,
            f"{file_date.year:04d}",
            f"{file_date.month:02d}",
            f"{file_date.day:02d}"
        )
        ensure_dir(dir_path)

        target_file = os.path.join(dir_path, item["filename"])

        if download_file(
            item["file_url"],
            target_file,
            args.timeout,
            args.max_retries,
            args.retry_backoff,
            args.rate_limit_backoff
        ):
            downloaded += 1
            logger.info(f"Downloaded: {target_file}")
        else:
            skipped += 1

    logger.info(f"Finished. Downloaded: {downloaded}, skipped: {skipped}")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    args = parse_args()
    process_files(args)