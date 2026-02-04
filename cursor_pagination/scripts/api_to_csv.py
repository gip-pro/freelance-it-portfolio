#!/usr/bin/env python3
import time
import csv
import requests
from typing import Dict, List, Any, Optional

API_URL = "https://api.example.com/v1/resources"
API_TOKEN = "PUT_YOUR_API_TOKEN_HERE"

OUTPUT_CSV = "output.csv"

PAGE_SIZE = 100
REQUESTS_PER_SECOND = 5
MAX_RETRIES = 5
TIMEOUT_SECONDS = 30


class RateLimiter:
    def __init__(self, rate_per_sec: int):
        self.delay = 1.0 / rate_per_sec
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_call = time.time()


def fetch_page(
    session: requests.Session,
    page: int,
    page_size: int
) -> List[Dict[str, Any]]:
    params = {
        "page": page,
        "page_size": page_size
    }

    for attempt in range(1, MAX_RETRIES + 1):
        response = session.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)

        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])

        if response.status_code in (429, 500, 502, 503, 504):
            backoff = 2 ** attempt
            time.sleep(backoff)
            continue

        response.raise_for_status()

    raise RuntimeError(f"Failed to fetch page {page} after {MAX_RETRIES} retries")


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    fieldnames = rows[0].keys()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    })

    rate_limiter = RateLimiter(REQUESTS_PER_SECOND)

    all_items: List[Dict[str, Any]] = []
    page = 1

    while True:
        rate_limiter.wait()
        items = fetch_page(session, page, PAGE_SIZE)

        if not items:
            break

        all_items.extend(items)
        page += 1

    write_csv(OUTPUT_CSV, all_items)


if __name__ == "__main__":
    main()