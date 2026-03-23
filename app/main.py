"""
MLOps Sentiment Analyzer — FastAPI Application

A production-grade REST API serving a HuggingFace sentiment analysis model.
Includes health checks, batch predictions, Prometheus metrics, and model info.
"""

import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.model import (
    model,
    MODEL_NAME,
    MODEL_VERSION,
    MODEL_TASK,
    MAX_INPUT_LENGTH,
    SUPPORTED_LABELS,
)
from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    SentimentResult,
    HealthResponse,
    ModelInfoResponse,
)
from app.metrics import BATCH_SIZE

# ──────────────────────── Logging ────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────── App Startup / Shutdown ────────────────────────

APP_START_TIME: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the AI model on startup, cleanup on shutdown."""
    global APP_START_TIME
    APP_START_TIME = time.time()

    logger.info("Starting MLOps Sentiment Analyzer...")
    model.load()
    logger.info("Application ready to serve predictions!")

    yield  # App is running

    logger.info("Shutting down MLOps Sentiment Analyzer...")


# ──────────────────────── FastAPI App ────────────────────────

app = FastAPI(
    title="MLOps Sentiment Analyzer",
    description=(
        "Production-grade AI sentiment analysis API. "
        "Deployed on AWS EKS with ArgoCD GitOps, Terraform IaC, "
        "and Prometheus/Grafana monitoring."
    ),
    version=MODEL_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (allow all for demo; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files directory if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ──────────────────────── Endpoints ────────────────────────


@app.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(request: PredictionRequest):
    """
    Run sentiment analysis on a single text.

    Returns the predicted sentiment (POSITIVE/NEGATIVE),
    confidence score, and inference latency.
    """
    try:
        result = model.predict(request.text)

        return PredictionResponse(
            text=request.text,
            sentiment=result["sentiment"],
            confidence=result["confidence"],
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            latency_ms=result["latency_ms"],
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Model not ready: {e}")
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post(
    "/predict/batch", response_model=BatchPredictionResponse, tags=["Predictions"]
)
async def predict_batch(request: BatchPredictionRequest):
    """
    Run sentiment analysis on a batch of texts (max 32).

    More efficient than calling /predict multiple times.
    """
    try:
        BATCH_SIZE.set(len(request.texts))
        start_time = time.perf_counter()

        raw_results = model.predict_batch(request.texts)
        total_latency_ms = (time.perf_counter() - start_time) * 1000

        results = [
            SentimentResult(
                text=r["text"],
                sentiment=r["sentiment"],
                confidence=r["confidence"],
                latency_ms=r["latency_ms"],
            )
            for r in raw_results
        ]

        return BatchPredictionResponse(
            results=results,
            total_texts=len(results),
            total_latency_ms=round(total_latency_ms, 2),
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Model not ready: {e}")
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.

    Returns model status and uptime information.
    """
    uptime = time.time() - APP_START_TIME if APP_START_TIME > 0 else 0.0

    status = "healthy" if model.is_loaded else "unhealthy"
    status_code = 200 if model.is_loaded else 503

    return JSONResponse(
        status_code=status_code,
        content=HealthResponse(
            status=status,
            model_loaded=model.is_loaded,
            model_name=MODEL_NAME if model.is_loaded else None,
            model_version=MODEL_VERSION,
            uptime_seconds=round(uptime, 2),
        ).model_dump(),
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Operations"])
async def model_info():
    """
    Get detailed information about the currently loaded AI model.
    """
    if not model.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return ModelInfoResponse(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_task=MODEL_TASK,
        max_input_length=MAX_INPUT_LENGTH,
        supported_labels=SUPPORTED_LABELS,
        device=model.device,
        total_predictions=model.total_predictions,
    )


@app.get("/metrics", tags=["Operations"], include_in_schema=False)
async def metrics():
    """
    Prometheus metrics endpoint.

    Scraped by Prometheus to collect prediction latency,
    throughput, confidence scores, and model health metrics.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/api/info", tags=["General"])
async def api_info():
    """Information endpoint with API metadata."""
    return {
        "service": "MLOps Sentiment Analyzer",
        "version": MODEL_VERSION,
        "description": "AI-powered sentiment analysis API",
        "docs": "/docs",
        "health": "/health",
        "model_info": "/model/info",
        "status": "running",
    }


@app.get("/", tags=["General"])
async def root():
    """Root endpoint serves the Web GUI."""
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return await api_info()
