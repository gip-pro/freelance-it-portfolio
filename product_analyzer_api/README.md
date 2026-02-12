# Product Analyzer API

Production-ready FastAPI service that accepts an image URL and returns:
- product name
- category
- estimated market price
- confidence score

## Project structure

```text
product_analyzer_api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   ├── main.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       └── vision_client.py
├── vba/
│   └── AnalyzeProduct.bas
├── .env.example
├── requirements.txt
└── README.md
```

## 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `VISION_API_KEY`.

## 2) Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3) Request example

```bash
curl -X POST http://localhost:8000/analyze-product \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://example.com/product.jpg"}'
```

## 4) Response example

```json
{
  "success": true,
  "data": {
    "product_name": "Apple iPhone 14",
    "category": "Smartphones",
    "estimated_market_price": 699.0,
    "currency": "USD",
    "confidence": 0.86
  }
}
```

## 5) Deploy notes

- Use a process manager (systemd, Supervisor, Docker, Kubernetes).
- Set env variables in your deployment platform secrets manager.
- Run behind Nginx/Traefik with HTTPS.
- Restrict `CORS_ALLOW_ORIGINS` in production.
