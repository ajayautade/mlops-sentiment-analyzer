"""
Pydantic V2 schemas for request/response models.
Used by FastAPI for automatic validation, serialization, and OpenAPI docs.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ──────────────────────── Request Models ────────────────────────


class PredictionRequest(BaseModel):
    """Request body for sentiment prediction."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to analyze for sentiment",
        examples=["I absolutely love this product! It exceeded all my expectations."],
    )


class BatchPredictionRequest(BaseModel):
    """Request body for batch sentiment predictions."""

    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=32,
        description="List of texts to analyze (max 32 per batch)",
    )


# ──────────────────────── Response Models ────────────────────────


class SentimentResult(BaseModel):
    """Individual sentiment analysis result."""

    text: str = Field(..., description="Original input text")
    sentiment: str = Field(
        ..., description="Predicted sentiment label (POSITIVE/NEGATIVE)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the prediction"
    )
    latency_ms: float = Field(..., description="Inference time in milliseconds")


class PredictionResponse(BaseModel):
    """Response for a single prediction request."""

    text: str
    sentiment: str
    confidence: float
    model_name: str
    model_version: str
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchPredictionResponse(BaseModel):
    """Response for a batch prediction request."""

    results: list[SentimentResult]
    total_texts: int
    total_latency_ms: float
    model_name: str
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(..., description="Service health status")
    model_loaded: bool = Field(
        ..., description="Whether the AI model is loaded and ready"
    )
    model_name: Optional[str] = Field(None, description="Name of the loaded model")
    model_version: str = Field(
        ..., description="Version of the model serving application"
    )
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class ModelInfoResponse(BaseModel):
    """Response for model information endpoint."""

    model_name: str
    model_version: str
    model_task: str
    max_input_length: int
    supported_labels: list[str]
    device: str
    total_predictions: int
