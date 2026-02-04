import argparse
import csv
import json
import logging
import os
import time
from typing import Dict, List, Optional

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("collector.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_state(state_path: str) -> Optional[str]:
    if not os.path.isfile(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cursor")

def save_state(state_path: str, cursor: Optional[str]):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump({"cursor": cursor}, f)

def fetch_page(
    url: str,
    cursor: Optional[str],
    retries: int,
    retry_delay: int
) -> Optional[Dict]:
    params = {}
    if cursor:
        params["cursor"] = cursor

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", retry_delay))
                logger.warning(f"Rate limit (429). Ожидание {retry_after} сек.")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except (Timeout, ConnectionError) as e:
            logger.warning(
                f"Сетевая ошибка (попытка {attempt}/{retries}): {e}. "
                f"Повтор через {retry_delay} сек."
            )
            time.sleep(retry_delay)
        except RequestException as e:
            logger.error(f"Критическая ошибка запроса: {e}")
            return None

    return None

def write_csv(path: str, rows: List[Dict], write_header: bool) -> int:
    if not rows:
        return 0

    fieldnames = rows[0].keys()

    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        writer.writerows(rows)

    return len(rows)

def main():
    parser = argparse.ArgumentParser(
        description="CLI скрипт для cursor-based пагинации с поддержкой возобновления"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL REST API"
    )
    parser.add_argument(
        "--output",
        default="data.csv",
        help="CSV файл для данных"
    )
    parser.add_argument(
        "--state-file",
        default="state.json",
        help="Файл состояния курсора"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=1,
        help="Задержка между запросами (сек)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Количество повторов при ошибках"
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="Задержка между retry (сек)"
    )

    args = parser.parse_args()

    cursor = load_state(args.state_file)
    logger.info(f"Старт с курсора: {cursor}")

    total_rows = 0
    first_write = not os.path.isfile(args.output)

    while True:
        response = fetch_page(
            url=args.url,
            cursor=cursor,
            retries=args.retries,
            retry_delay=args.retry_delay
        )

        if response is None:
            logger.error("Прерывание из-за ошибки API")
            break

        items = response.get("items", [])
        next_cursor = response.get("next_cursor")

        if not items:
            logger.info("Данные закончились")
            break

        written = write_csv(
            path=args.output,
            rows=items,
            write_header=first_write
        )
        first_write = False

        total_rows += written
        logger.info(f"Записано строк: {written}")

        save_state(args.state_file, next_cursor)
        logger.info(f"Курсор сохранён: {next_cursor}")

        if not next_cursor:
            logger.info("next_cursor отсутствует. Завершение.")
            break

        cursor = next_cursor
        time.sleep(args.delay)

    logger.info("=== ИТОГ ===")
    logger.info(f"Всего записано строк: {total_rows}")
    logger.info(f"CSV файл: {args.output}")
    logger.info(f"Файл состояния: {args.state_file}")

if __name__ == "__main__":
    main()