# ──────────────────────────────────────────────────────────────
# MLOps Sentiment Analyzer — Multi-Stage Docker Build
# ──────────────────────────────────────────────────────────────
# Stage 1: Download model & install dependencies
# Stage 2: Slim production image
# ──────────────────────────────────────────────────────────────

# ==================== Stage 1: Builder ====================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps needed for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
# We install CPU-only PyTorch first (from PyTorch's CPU wheel index)
# because our EKS nodes don't have GPUs, so the full CUDA-enabled
# PyTorch (~800MB) is unnecessary. CPU-only is ~200MB — smaller image,
# faster builds, and avoids download timeouts.
COPY requirements.txt download_model.py .
RUN pip install --no-cache-dir --prefix=/install \
    torch==2.6.0+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Pre-download the HuggingFace model during build
# This avoids downloading on every container start (faster cold starts)
ENV PYTHONPATH=/install/lib/python3.12/site-packages:$PYTHONPATH
RUN python download_model.py


# ==================== Stage 2: Production ====================
FROM python:3.12-slim AS production

# Metadata
LABEL maintainer="Ajay Autade"
LABEL description="MLOps Sentiment Analyzer — AI Model Serving API"
LABEL version="1.0.0"

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy the pre-downloaded model cache from builder
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Copy application code
COPY app/ ./app/

# Create non-root user for security (best practice)
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy model cache to the non-root user's home
RUN mkdir -p /home/appuser/.cache && \
    cp -r /root/.cache/huggingface /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chown -R appuser:appuser /app && \
    rm -rf /root/.cache

USER appuser

# Environment variables
ENV APP_VERSION=1.0.0
ENV APP_ENV=production
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface

# Expose port
EXPOSE 8080

# Health check (used by Docker and Kubernetes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with uvicorn (production ASGI server)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
