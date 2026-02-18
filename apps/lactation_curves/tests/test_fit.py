"""Tests for the /fit endpoint (lactation curve fitting)."""

import httpx
import pytest


def test_fit_wood_returns_305_predictions(api: httpx.Client, sample_data: dict):
    r = api.post("/fit", json={**sample_data, "model": "wood"})
    assert r.status_code == 200
    data = r.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 305
    assert all(isinstance(v, float) for v in data["predictions"])


def test_fit_defaults(api: httpx.Client, sample_data: dict):
    """Only required fields — all defaults should work."""
    r = api.post("/fit", json=sample_data)
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 305


@pytest.mark.parametrize("model", [
    "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot",
])
def test_fit_all_models(api: httpx.Client, sample_data: dict, model: str):
    r = api.post("/fit", json={**sample_data, "model": model})
    assert r.status_code == 200
    assert len(r.json()["predictions"]) >= 305
