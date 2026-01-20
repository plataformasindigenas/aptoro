"""Pytest fixtures for aptoro tests."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_schema_path(fixtures_dir: Path) -> Path:
    """Return path to sample schema."""
    return fixtures_dir / "sample_schema.yaml"


@pytest.fixture
def sample_csv_path(fixtures_dir: Path) -> Path:
    """Return path to sample CSV data."""
    return fixtures_dir / "sample_data.csv"


@pytest.fixture
def sample_json_path(fixtures_dir: Path) -> Path:
    """Return path to sample JSON data."""
    return fixtures_dir / "sample_data.json"


@pytest.fixture
def base_schema_path(fixtures_dir: Path) -> Path:
    """Return path to base schema for inheritance testing."""
    return fixtures_dir / "base_schema.yaml"


@pytest.fixture
def child_schema_path(fixtures_dir: Path) -> Path:
    """Return path to child schema for inheritance testing."""
    return fixtures_dir / "child_schema.yaml"
