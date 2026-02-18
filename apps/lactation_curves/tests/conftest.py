"""Shared fixtures for lactation_curves API tests.

Start the server first:  just run
Then run tests:          just test-api

Or test against deployed:
  API_BASE_URL=https://milkbot-dev-func.azurewebsites.net just test-api
"""

import os

import httpx
import pytest

@pytest.fixture
def sample_data() -> dict[str, list[int] | list[float]]:
    """Sample test-day milk recording data."""
    return {
        "dim": [10, 30, 60, 90, 120, 150, 200, 250, 305],
        "milkrecordings": [
            15.0, 25.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0,
        ],
    }


@pytest.fixture
def base_url() -> str:
    """Base URL of the running API.

    Defaults to local dev server. Override with API_BASE_URL env var
    to test against a deployed instance.
    """
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def api(base_url: str) -> httpx.Client:
    """HTTP client pointed at the running API."""
    return httpx.Client(base_url=base_url, timeout=30)
