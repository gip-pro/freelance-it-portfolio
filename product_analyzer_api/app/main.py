import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_config import configure_logging
from app.models import AnalyzeProductRequest, AnalyzeProductResponse, ErrorResponse
from app.services.vision_client import VisionAPIError, analyze_product_image

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    logger.warning("HTTP error: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=str(exc.detail)).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Internal server error").model_dump(),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze-product", response_model=AnalyzeProductResponse)
async def analyze_product(payload: AnalyzeProductRequest) -> AnalyzeProductResponse:
    image_url = str(payload.image_url)
    logger.info("Received analyze request for URL: %s", image_url)

    try:
        result = await analyze_product_image(image_url=image_url, settings=settings)
        return AnalyzeProductResponse(data=result)
    except VisionAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
