"""Shared fixtures for lactation_curves API tests."""

import os

import pytest
import httpx


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
