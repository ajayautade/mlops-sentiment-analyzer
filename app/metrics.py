"""
Custom Prometheus metrics for monitoring AI model performance.
These metrics are scraped by Prometheus and visualized in Grafana.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ──────────────────────── Counters ────────────────────────

# Total number of prediction requests (by sentiment label and status)
PREDICTION_REQUESTS_TOTAL = Counter(
    "prediction_requests_total",
    "Total number of prediction requests",
    labelnames=["sentiment", "status"],
)

# Total number of errors
PREDICTION_ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total number of prediction errors",
    labelnames=["error_type"],
)


# ──────────────────────── Histograms ────────────────────────

# Inference latency distribution (in seconds)
PREDICTION_LATENCY_SECONDS = Histogram(
    "prediction_latency_seconds",
    "Time spent on model inference",
    labelnames=["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
)

# Request size (number of characters in input text)
REQUEST_TEXT_LENGTH = Histogram(
    "request_text_length_chars",
    "Length of input text in characters",
    buckets=(10, 50, 100, 250, 500, 1000, 2500, 5000),
)

# Confidence score distribution
PREDICTION_CONFIDENCE = Histogram(
    "prediction_confidence_score",
    "Distribution of prediction confidence scores",
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0),
)


# ──────────────────────── Gauges ────────────────────────

# Model loading time
MODEL_LOAD_TIME_SECONDS = Gauge(
    "model_load_time_seconds",
    "Time taken to load the AI model",
)

# Whether the model is currently loaded and ready
MODEL_READY = Gauge(
    "model_ready",
    "Whether the AI model is loaded and ready for inference (1=ready, 0=not ready)",
)

# Number of texts in the last batch request
BATCH_SIZE = Gauge(
    "batch_request_size",
    "Number of texts in the last batch prediction request",
)


# ──────────────────────── Info ────────────────────────

# Model metadata
MODEL_INFO = Info(
    "ai_model",
    "Information about the currently loaded AI model",
)
