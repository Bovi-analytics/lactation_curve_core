"""Shared fixtures for lactation curve tests."""

import os
from pathlib import Path

import pytest
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

REPO_ROOT = Path(__file__).resolve().parents[1]


def milkbot_key() -> str:
    """Return the MilkBot API key from environment."""
    key = os.getenv("milkbot_key")
    if not key:
        raise ValueError("milkbot_key not found in environment. Check your .env file.")
    return key


@pytest.fixture
def key() -> str:
    """Fixture providing the MilkBot API key."""
    return milkbot_key()


@pytest.fixture
def test_data_dir() -> Path:
    """Return directory containing CSV fixtures for lactation tests."""
    return REPO_ROOT / "tests" / "lactationcurve" / "test_data"


@pytest.fixture
def package_data_dir() -> Path:
    """Return package data directory with default lactation assets."""
    return REPO_ROOT / "packages" / "python" / "lactation" / "data"
