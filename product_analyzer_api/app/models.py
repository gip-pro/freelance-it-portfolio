from pydantic import AnyHttpUrl, BaseModel, Field


class AnalyzeProductRequest(BaseModel):
    image_url: AnyHttpUrl = Field(..., description="Publicly accessible image URL")


class AnalyzeProductResult(BaseModel):
    product_name: str = Field(..., description="Detected product name")
    category: str = Field(..., description="Detected category")
    estimated_market_price: float = Field(..., ge=0, description="Estimated market price")
    currency: str = Field(default="USD")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0..1")


class AnalyzeProductResponse(BaseModel):
    success: bool = True
    data: AnalyzeProductResult


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
