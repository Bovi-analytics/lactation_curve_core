"""Tests for the /predict endpoint (MilkBot direct evaluation)."""

import httpx


def test_predict_returns_predictions(api: httpx.Client):
    r = api.post("/predict", json={
        "t": [1, 30, 60, 90, 120, 150, 200, 250, 305],
        "a": 40.0,
        "b": 20.0,
        "c": 0.5,
        "d": 0.003,
    })
    assert r.status_code == 200
    data = r.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 9
    assert all(isinstance(v, float) for v in data["predictions"])


def test_predict_missing_field(api: httpx.Client):
    r = api.post("/predict", json={"t": [1, 30], "a": 40.0})
    assert r.status_code == 422
