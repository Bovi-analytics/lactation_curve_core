"""Tests for the /characteristic endpoint."""

import httpx
import pytest


def test_characteristic_cumulative(api: httpx.Client, sample_data: dict):
    r = api.post("/characteristic", json={
        **sample_data,
        "characteristic": "cumulative_milk_yield",
    })
    assert r.status_code == 200
    data = r.json()
    assert "value" in data
    assert isinstance(data["value"], float)
    assert data["value"] > 0


def test_characteristic_peak_yield(api: httpx.Client, sample_data: dict):
    r = api.post("/characteristic", json={
        **sample_data,
        "characteristic": "peak_yield",
    })
    assert r.status_code == 200
    assert r.json()["value"] > 0


def test_characteristic_time_to_peak(api: httpx.Client, sample_data: dict):
    r = api.post("/characteristic", json={
        **sample_data,
        "characteristic": "time_to_peak",
    })
    assert r.status_code == 200
    value = r.json()["value"]
    assert 0 < value < 305


def test_characteristic_persistency(api: httpx.Client, sample_data: dict):
    r = api.post("/characteristic", json={
        **sample_data,
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
    api: httpx.Client, sample_data: dict, characteristic: str,
):
    r = api.post("/characteristic", json={
        **sample_data,
        "characteristic": characteristic,
    })
    assert r.status_code == 200
    assert isinstance(r.json()["value"], float)


def test_characteristic_defaults(api: httpx.Client, sample_data: dict):
    """Only required fields — all defaults should work."""
    r = api.post("/characteristic", json=sample_data)
    assert r.status_code == 200
    assert isinstance(r.json()["value"], float)
