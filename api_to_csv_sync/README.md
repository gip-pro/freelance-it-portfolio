# API → CSV Sync

Python-скрипт для идемпотентной синхронизации данных REST API с CSV-файлом.
Оптимизирован для запуска через cron с корректными exit-кодами.

## Возможности
- CLI-параметры для API URL и пути CSV
- Идемпотентная синхронизация по ID
- Обновление и добавление записей
- Отдельная обработка сетевых ошибок
- Валидация структуры API-ответа
- Детальное логирование

## Использование

Пример ручного запуска:

python api_to_csv_sync.py --api-url https://jsonplaceholder.typicode.com/posts --csv-path data.csv

## Cron

Каждые 10 минут:

*/10 * * * * /usr/bin/python3 /path/api_to_csv_sync.py --api-url https://jsonplaceholder.typicode.com/posts --csv-path /path/data.csv

## Exit codes

- 0 — успех
- 1 — общая ошибка
- 2 — ошибка API
- 3 — ошибка структуры данных
- 4 — ошибка чтения/записи файлов

## Требования
- Python 3.9+
- requests
