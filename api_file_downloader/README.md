# API File Downloader

Python-скрипт для загрузки файлов из REST API и упорядочивания их по дате.
Оптимизирован для регулярного серверного запуска.

## Возможности
- CLI-настройка timeout и retry
- Отдельная обработка HTTP 429 (rate limit)
- Безопасная загрузка через tmp-файл с последующим rename
- Пропуск уже загруженных файлов
- Организация каталогов ГГГГ/ММ/ДД
- Детальное логирование

## Использование

Пример запуска:

python api_file_downloader.py \
  --api-url https://api.example.com/v1/files \
  --output-dir downloads \
  --timeout 20 \
  --max-retries 5 \
  --retry-backoff 5 \
  --rate-limit-backoff 30

## Exit codes
- 0 — успех
- 2 — ошибка API
- 3 — ошибка ввода/вывода
- 4 — rate limit

## Требования
- Python 3.9+
- requests

## Логи
Файл логов: downloader.log