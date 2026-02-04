import argparse
import csv
import logging
import os
import requests
import time
from typing import List, Dict, Optional
from requests.exceptions import Timeout, ConnectionError, RequestException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_page(
    url: str,
    page: int,
    limit: int,
    retries: int,
    retry_delay: int
) -> Optional[List[Dict]]:
    params = {
        "_page": page,
        "_limit": limit
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", retry_delay))
                logger.warning(f"429 Too Many Requests. Ожидание {retry_after} сек.")
                time.sleep(retry_after)
                continue

            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list):
                logger.error("Ответ API не является списком")
                return None

            return data

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

def write_failed_page(path: str, page: int, reason: str):
    file_exists = os.path.isfile(path)

    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["page", "reason"])
        writer.writerow([page, reason])

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
    parser = argparse.ArgumentParser(description="CLI загрузчик данных с пагинацией")
    parser.add_argument(
        "--url",
        default=os.getenv("API_URL", "https://jsonplaceholder.typicode.com/posts"),
        help="URL API"
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT_PATH", "data.csv"),
        help="CSV файл"
    )
    parser.add_argument(
        "--failed-pages",
        default="failed_pages.csv",
        help="CSV файл для ошибок страниц"
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=50,
        help="Размер страницы (_limit)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=1,
        help="Задержка между страницами (сек)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Количество повторов при ошибке"
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="Задержка между retry (сек)"
    )

    args = parser.parse_args()

    page = 1
    total_rows = 0
    total_pages = 0
    file_exists = os.path.isfile(args.output)

    while True:
        logger.info(f"Загрузка страницы {page}")

        data = fetch_page(
            url=args.url,
            page=page,
            limit=args.page_size,
            retries=args.retries,
            retry_delay=args.retry_delay
        )

        if data is None:
            logger.error(f"Страница {page} не загружена")
            write_failed_page(args.failed_pages, page, "request_failed")
            page += 1
            time.sleep(args.delay)
            continue

        if not data:
            logger.info("Пустой ответ. Завершение пагинации.")
            break

        written = write_csv(
            path=args.output,
            rows=data,
            write_header=not file_exists and page == 1
        )

        total_rows += written
        total_pages += 1

        logger.info(f"Страница {page}: записано {written} строк")

        if written < args.page_size:
            logger.info("Последняя страница достигнута")
            break

        page += 1
        time.sleep(args.delay)

    logger.info("=== ИТОГ ===")
    logger.info(f"Страниц обработано: {total_pages}")
    logger.info(f"Строк записано: {total_rows}")
    logger.info(f"Файл данных: {args.output}")
    logger.info(f"Файл ошибок: {args.failed_pages}")

if __name__ == "__main__":
    main()