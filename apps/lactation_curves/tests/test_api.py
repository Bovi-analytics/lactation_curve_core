"""Integration tests for the Lactation Curves API.

Start the server first:  just run
Then run tests:          just test-api

Or test against deployed:
  API_BASE_URL=https://milkbot-dev-func.azurewebsites.net just test-api
"""

import httpx
import pytest

DIM = [10, 30, 60, 90, 120, 150, 200, 250, 305]
MILK = [15.0, 25.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0]


# --- Health ---


def test_health(api: httpx.Client):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- /predict ---


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


# --- /fit ---


def test_fit_wood_returns_305_predictions(api: httpx.Client):
    r = api.post("/fit", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "model": "wood",
    })
    assert r.status_code == 200
    data = r.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 305
    assert all(isinstance(v, float) for v in data["predictions"])


def test_fit_milkbot(api: httpx.Client):
    r = api.post("/fit", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "model": "milkbot",
    })
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 305


def test_fit_defaults(api: httpx.Client):
    """Only required fields — all defaults should work."""
    r = api.post("/fit", json={
        "dim": DIM,
        "milkrecordings": MILK,
    })
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 305


@pytest.mark.parametrize("model", [
    "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot",
])
def test_fit_all_models(api: httpx.Client, model: str):
    r = api.post("/fit", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "model": model,
    })
    assert r.status_code == 200
    assert len(r.json()["predictions"]) >= 305


# --- /characteristic ---


def test_characteristic_cumulative(api: httpx.Client):
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "characteristic": "cumulative_milk_yield",
    })
    assert r.status_code == 200
    data = r.json()
    assert "value" in data
    assert isinstance(data["value"], float)
    assert data["value"] > 0


def test_characteristic_peak_yield(api: httpx.Client):
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "characteristic": "peak_yield",
    })
    assert r.status_code == 200
    assert r.json()["value"] > 0


def test_characteristic_time_to_peak(api: httpx.Client):
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "characteristic": "time_to_peak",
    })
    assert r.status_code == 200
    value = r.json()["value"]
    assert 0 < value < 305


def test_characteristic_persistency(api: httpx.Client):
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "characteristic": "persistency",
    })
    assert r.status_code == 200
    assert isinstance(r.json()["value"], float)


@pytest.mark.parametrize("characteristic", [
    "time_to_peak",
    "peak_yield",
    "cumulative_milk_yield",
    "persistency",
])
def test_characteristic_all_types(
    api: httpx.Client, characteristic: str,
):
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
        "characteristic": characteristic,
    })
    assert r.status_code == 200
    assert isinstance(r.json()["value"], float)


def test_characteristic_defaults(api: httpx.Client):
    """Only required fields — all defaults should work."""
    r = api.post("/characteristic", json={
        "dim": DIM,
        "milkrecordings": MILK,
    })
    assert r.status_code == 200
    assert isinstance(r.json()["value"], float)
