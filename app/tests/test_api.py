"""
API endpoint tests for the MLOps Sentiment Analyzer.
Uses FastAPI's TestClient (backed by httpx) for integration testing.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client. Model loads once for all tests in this module."""
    with TestClient(app) as c:
        yield c


# ──────────────────────── Root Endpoint ────────────────────────


class TestRootEndpoint:
    def test_root_returns_service_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "MLOps Sentiment Analyzer"
        assert "version" in data
        assert data["status"] == "running"


# ──────────────────────── Health Endpoint ────────────────────────


class TestHealthEndpoint:
    def test_health_check_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

    def test_health_check_contains_uptime(self, client):
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


# ──────────────────────── Prediction Endpoint ────────────────────────


class TestPredictEndpoint:
    def test_predict_positive_sentiment(self, client):
        response = client.post(
            "/predict",
            json={"text": "I absolutely love this product! It's amazing!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "POSITIVE"
        assert data["confidence"] > 0.5
        assert data["latency_ms"] > 0
        assert data["model_name"] is not None

    def test_predict_negative_sentiment(self, client):
        response = client.post(
            "/predict",
            json={"text": "This is terrible. I hate it so much."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "NEGATIVE"
        assert data["confidence"] > 0.5

    def test_predict_returns_model_info(self, client):
        response = client.post(
            "/predict",
            json={"text": "This is a test."},
        )
        data = response.json()
        assert "model_name" in data
        assert "model_version" in data
        assert "timestamp" in data

    def test_predict_empty_text_returns_422(self, client):
        response = client.post("/predict", json={"text": ""})
        assert response.status_code == 422

    def test_predict_missing_text_returns_422(self, client):
        response = client.post("/predict", json={})
        assert response.status_code == 422


# ──────────────────────── Batch Prediction Endpoint ────────────────────────


class TestBatchPredictEndpoint:
    def test_batch_predict_multiple_texts(self, client):
        response = client.post(
            "/predict/batch",
            json={
                "texts": [
                    "I love this!",
                    "I hate this!",
                    "This is okay.",
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_texts"] == 3
        assert len(data["results"]) == 3
        assert data["total_latency_ms"] > 0

    def test_batch_predict_single_text(self, client):
        response = client.post(
            "/predict/batch",
            json={"texts": ["Great product!"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_texts"] == 1

    def test_batch_predict_empty_list_returns_422(self, client):
        response = client.post("/predict/batch", json={"texts": []})
        assert response.status_code == 422


# ──────────────────────── Model Info Endpoint ────────────────────────


class TestModelInfoEndpoint:
    def test_model_info_returns_details(self, client):
        response = client.get("/model/info")
        assert response.status_code == 200
        data = response.json()
        assert data["model_task"] == "sentiment-analysis"
        assert "POSITIVE" in data["supported_labels"]
        assert "NEGATIVE" in data["supported_labels"]
        assert data["max_input_length"] > 0

    def test_model_info_tracks_predictions(self, client):
        # Make a prediction first
        client.post("/predict", json={"text": "test"})
        response = client.get("/model/info")
        data = response.json()
        assert data["total_predictions"] > 0


# ──────────────────────── Metrics Endpoint ────────────────────────


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_prometheus_format(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Prometheus metrics should contain our custom metrics
        assert "prediction_requests_total" in content
        assert "prediction_latency_seconds" in content
        assert "model_ready" in content
