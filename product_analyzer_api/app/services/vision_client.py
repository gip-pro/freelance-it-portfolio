import json
import logging

import httpx

from app.config import Settings
from app.models import AnalyzeProductResult

logger = logging.getLogger(__name__)


class VisionAPIError(Exception):
    pass


async def analyze_product_image(image_url: str, settings: Settings) -> AnalyzeProductResult:
    headers = {
        "Authorization": f"Bearer {settings.vision_api_key}",
        "Content-Type": "application/json",
    }

    prompt = (
        "Analyze the product in the image and return only JSON with keys: "
        "product_name (string), category (string), estimated_market_price (number), "
        "currency (string), confidence (number from 0 to 1)."
    )

    payload = {
        "model": settings.vision_model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(settings.vision_api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
    except httpx.TimeoutException as exc:
        logger.exception("Vision API timeout")
        raise VisionAPIError("Vision API request timed out") from exc
    except httpx.HTTPStatusError as exc:
        logger.exception("Vision API returned non-success status: %s", exc.response.status_code)
        raise VisionAPIError("Vision API returned an error response") from exc
    except httpx.RequestError as exc:
        logger.exception("Vision API network error")
        raise VisionAPIError("Unable to reach Vision API") from exc

    try:
        text_output = response_json["output"][0]["content"][0]["text"]
        parsed = json.loads(text_output)
        return AnalyzeProductResult(**parsed)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        logger.exception("Unexpected Vision API response format")
        raise VisionAPIError("Vision API returned an invalid payload format") from exc
    except Exception as exc:
        logger.exception("Vision API payload validation error")
        raise VisionAPIError("Vision API payload could not be validated") from exc
