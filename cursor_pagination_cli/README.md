# Cursor Pagination CLI

CLI-утилита для выгрузки данных из API с cursor-based пагинацией в CSV.
README очищен от конструкций, которые могут ломать CDATA.

## Быстрый старт

Простой запуск:

    python cursor_pagination_cli.py --url https://api.example.com/v1/items --token YOUR_TOKEN --output data.csv

С конфигурируемым backoff для HTTP 429:

    python cursor_pagination_cli.py --url https://api.example.com/v1/items --backoff-429 30

## Параметры

- --url — endpoint API (обязательно)
- --output — CSV файл (по умолчанию data.csv)
- --fields — список полей CSV через запятую
- --token — Bearer-токен
- --max-items — лимит строк
- --timeout — таймаут запроса в секундах
- --backoff-429 — пауза при HTTP 429 в секундах
- --dry-run — без записи файлов

## Формат ответа API

Пример корректного ответа:

{
  "items": [
    { "id": 1, "name": "Item A" },
    { "id": 2, "name": "Item B" }
  ],
  "next_cursor": "eyJpZCI6Mn0="
}

## Exit codes

- 0 — успех
- 1 — ошибка выполнения или запроса
- 2 — некорректный формат ответа API
- 3 — ошибка записи файлов