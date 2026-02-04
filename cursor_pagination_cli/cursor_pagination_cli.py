import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("collector.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INVALID_API = 2
EXIT_IO = 3


def check_write_access(paths: List[str]):
    for p in paths:
        dir_n = os.path.dirname(p) or "."
        if (os.path.exists(p) and not os.access(p, os.W_OK)) or (
            not os.path.exists(p) and not os.access(dir_n, os.W_OK)
        ):
            logger.error(f"Access denied: {p}")
            sys.exit(EXIT_IO)


def validate(data: Any) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("items"), list)
        and (
            data.get("next_cursor") is None
            or isinstance(data.get("next_cursor"), str)
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Cursor Pagination CLI")
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", default="data.csv")
    parser.add_argument("--fields", help="CSV columns (comma-separated)")
    parser.add_argument("--token", help="Bearer Auth Token")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--max-pages", type=int, help="Fail-safe limit for pages")
    parser.add_argument("--page-delay", type=float, default=0.5, help="Delay between pages in seconds")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument(
        "--backoff-429",
        type=int,
        default=10,
        help="Backoff seconds for HTTP 429"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    state_f = "state.json"
    err_f = "failed_batches.csv"

    if not args.dry_run:
        check_write_access([args.output, state_f, err_f])

    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    cursor = None
    if os.path.exists(state_f):
        with open(state_f, "r", encoding="utf-8") as f:
            cursor = json.load(f).get("cursor")

    total = 0
    pages = 0
    start_t = time.perf_counter()
    fixed_fields = (
        [f.strip() for f in args.fields.split(",")]
        if args.fields else None
    )

    try:
        while True:
            if args.max_pages and pages >= args.max_pages:
                logger.error("Max pages limit reached")
                break

            try:
                response = requests.get(
                    args.url,
                    params={"cursor": cursor} if cursor else {},
                    headers=headers,
                    timeout=args.timeout
                )

                if response.status_code == 429:
                    logger.warning(
                        f"Rate limit. Waiting {args.backoff_429}s..."
                    )
                    time.sleep(args.backoff_429)
                    continue

                response.raise_for_status()
                data = response.json()

            except KeyboardInterrupt:
                logger.warning("Stopped by user")
                sys.exit(EXIT_ERROR)

            except Exception as e:
                logger.error(f"Request failed: {e}")
                with open(err_f, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()},{cursor},ERR\n")
                sys.exit(EXIT_ERROR)

            if not validate(data):
                logger.error("Invalid API format")
                sys.exit(EXIT_INVALID_API)

            items = data["items"]
            cursor = data.get("next_cursor")

            if not items:
                break

            pages += 1

            if not args.dry_run:
                is_new = not os.path.exists(args.output)
                with open(
                    args.output,
                    "a",
                    newline="",
                    encoding="utf-8"
                ) as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=fixed_fields or items[0].keys(),
                        extrasaction="ignore"
                    )
                    if is_new:
                        writer.writeheader()
                    writer.writerows(items)

                total += len(items)

                with open(state_f, "w", encoding="utf-8") as f:
                    json.dump({"cursor": cursor}, f)

            logger.info(
                f"Page {pages}: +{len(items)} rows. Total: {total}"
            )

            if not cursor or (
                args.max_items and total >= args.max_items
            ):
                break

            time.sleep(args.page_delay)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(EXIT_ERROR)

    duration = time.perf_counter() - start_t
    throughput = total / duration if duration > 0 else 0.0
    logger.info(
        "DONE: %s rows, %s pages, %.2fs total, %.2f rows/sec",
        total,
        pages,
        duration,
        throughput
    )

    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()