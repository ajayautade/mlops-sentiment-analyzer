"""
AI Model loading and inference logic.
Handles HuggingFace model lifecycle with singleton pattern and performance tracking.
"""

import time
import logging
from typing import Optional

from transformers import pipeline, Pipeline

from app.metrics import (
    MODEL_LOAD_TIME_SECONDS,
    MODEL_READY,
    MODEL_INFO,
    PREDICTION_LATENCY_SECONDS,
    PREDICTION_CONFIDENCE,
    PREDICTION_REQUESTS_TOTAL,
    PREDICTION_ERRORS_TOTAL,
    REQUEST_TEXT_LENGTH,
)

logger = logging.getLogger(__name__)

# ──────────────────────── Configuration ────────────────────────

MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
MODEL_VERSION = "1.0.0"
MODEL_TASK = "sentiment-analysis"
MAX_INPUT_LENGTH = 512
SUPPORTED_LABELS = ["POSITIVE", "NEGATIVE"]


# ──────────────────────── Singleton Model Manager ────────────────────────


class SentimentModel:
    """
    Singleton wrapper around the HuggingFace sentiment analysis pipeline.
    Manages model lifecycle, inference, and metrics tracking.
    """

    _instance: Optional["SentimentModel"] = None
    _pipeline: Optional[Pipeline] = None
    _is_loaded: bool = False
    _load_time: float = 0.0
    _total_predictions: int = 0

    def __new__(cls) -> "SentimentModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        """Load the HuggingFace model. Call once at application startup."""
        if self._is_loaded:
            logger.info("Model already loaded, skipping.")
            return

        logger.info(f"Loading model: {MODEL_NAME} ...")
        start_time = time.perf_counter()

        try:
            self._pipeline = pipeline(
                task=MODEL_TASK,
                model=MODEL_NAME,
                truncation=True,
                max_length=MAX_INPUT_LENGTH,
            )
            self._load_time = time.perf_counter() - start_time
            self._is_loaded = True

            # Record metrics
            MODEL_LOAD_TIME_SECONDS.set(self._load_time)
            MODEL_READY.set(1)
            MODEL_INFO.info(
                {
                    "name": MODEL_NAME,
                    "version": MODEL_VERSION,
                    "task": MODEL_TASK,
                    "device": str(self._pipeline.device),
                }
            )

            logger.info(
                f"Model loaded successfully in {self._load_time:.2f}s "
                f"on device: {self._pipeline.device}"
            )

        except Exception as e:
            MODEL_READY.set(0)
            PREDICTION_ERRORS_TOTAL.labels(error_type="model_load_failure").inc()
            logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, text: str) -> dict:
        """
        Run sentiment analysis on a single text.

        Returns:
            dict with keys: sentiment, confidence, latency_ms
        """
        if not self._is_loaded or self._pipeline is None:
            raise RuntimeError("Model is not loaded. Call load() first.")

        # Track input length
        REQUEST_TEXT_LENGTH.observe(len(text))

        start_time = time.perf_counter()

        try:
            result = self._pipeline(text)[0]
            latency = time.perf_counter() - start_time
            latency_ms = latency * 1000

            sentiment = result["label"]
            confidence = round(result["score"], 4)

            # Record metrics
            PREDICTION_LATENCY_SECONDS.labels(endpoint="/predict").observe(latency)
            PREDICTION_CONFIDENCE.observe(confidence)
            PREDICTION_REQUESTS_TOTAL.labels(
                sentiment=sentiment, status="success"
            ).inc()
            self._total_predictions += 1

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "latency_ms": round(latency_ms, 2),
            }

        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(error_type="inference_failure").inc()
            PREDICTION_REQUESTS_TOTAL.labels(
                sentiment="unknown", status="error"
            ).inc()
            logger.error(f"Inference error: {e}")
            raise

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """
        Run sentiment analysis on a batch of texts.

        Returns:
            List of dicts, each with keys: text, sentiment, confidence, latency_ms
        """
        if not self._is_loaded or self._pipeline is None:
            raise RuntimeError("Model is not loaded. Call load() first.")

        results = []
        for text in texts:
            result = self.predict(text)
            result["text"] = text
            results.append(result)

        return results

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def device(self) -> str:
        if self._pipeline is not None:
            return str(self._pipeline.device)
        return "not loaded"

    @property
    def total_predictions(self) -> int:
        return self._total_predictions

    @property
    def load_time(self) -> float:
        return self._load_time


# Module-level singleton instance
model = SentimentModel()
