"""
Unit tests for the AI model loading and inference logic.
Tests the SentimentModel class directly without the FastAPI layer.
"""

import pytest
from app.model import SentimentModel, SUPPORTED_LABELS


@pytest.fixture(scope="module")
def sentiment_model():
    """Load the model once and reuse across all tests in this module."""
    m = SentimentModel()
    m.load()
    return m


# ──────────────────────── Model Loading ────────────────────────


class TestModelLoading:
    def test_model_loads_successfully(self, sentiment_model):
        assert sentiment_model.is_loaded is True

    def test_model_load_time_is_recorded(self, sentiment_model):
        assert sentiment_model.load_time > 0

    def test_model_device_is_set(self, sentiment_model):
        device = sentiment_model.device
        assert device in ["cpu", "cuda", "mps"]

    def test_model_is_singleton(self):
        model1 = SentimentModel()
        model2 = SentimentModel()
        assert model1 is model2


# ──────────────────────── Single Prediction ────────────────────────


class TestSinglePrediction:
    def test_positive_text(self, sentiment_model):
        result = sentiment_model.predict("I love this product! It's fantastic!")
        assert result["sentiment"] == "POSITIVE"
        assert result["confidence"] > 0.9
        assert result["latency_ms"] > 0

    def test_negative_text(self, sentiment_model):
        result = sentiment_model.predict("This is awful. Worst purchase ever.")
        assert result["sentiment"] == "NEGATIVE"
        assert result["confidence"] > 0.9

    def test_result_keys(self, sentiment_model):
        result = sentiment_model.predict("Test text.")
        assert "sentiment" in result
        assert "confidence" in result
        assert "latency_ms" in result

    def test_sentiment_is_valid_label(self, sentiment_model):
        result = sentiment_model.predict("Some random text for testing.")
        assert result["sentiment"] in SUPPORTED_LABELS

    def test_confidence_range(self, sentiment_model):
        result = sentiment_model.predict("I feel great about this!")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_long_text_is_truncated_not_errored(self, sentiment_model):
        """Test that texts longer than max_length are handled gracefully."""
        long_text = "This is amazing! " * 500  # Way longer than 512 tokens
        result = sentiment_model.predict(long_text)
        assert result["sentiment"] in SUPPORTED_LABELS


# ──────────────────────── Batch Prediction ────────────────────────


class TestBatchPrediction:
    def test_batch_returns_correct_count(self, sentiment_model):
        texts = ["I love this!", "I hate this!", "This is okay."]
        results = sentiment_model.predict_batch(texts)
        assert len(results) == 3

    def test_batch_results_contain_text(self, sentiment_model):
        texts = ["Great!", "Terrible!"]
        results = sentiment_model.predict_batch(texts)
        assert results[0]["text"] == "Great!"
        assert results[1]["text"] == "Terrible!"

    def test_batch_mixed_sentiments(self, sentiment_model):
        texts = [
            "I absolutely love this product!",
            "This is the worst thing I've ever bought.",
        ]
        results = sentiment_model.predict_batch(texts)
        assert results[0]["sentiment"] == "POSITIVE"
        assert results[1]["sentiment"] == "NEGATIVE"

    def test_batch_single_item(self, sentiment_model):
        results = sentiment_model.predict_batch(["Single text."])
        assert len(results) == 1


# ──────────────────────── Prediction Counter ────────────────────────


class TestPredictionTracking:
    def test_prediction_counter_increments(self, sentiment_model):
        initial_count = sentiment_model.total_predictions
        sentiment_model.predict("Test prediction tracking.")
        assert sentiment_model.total_predictions == initial_count + 1
