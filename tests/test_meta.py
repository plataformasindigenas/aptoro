"""Tests for metadata handling."""

import json
from pathlib import Path

import pytest

from aptoro import load_meta
from aptoro.errors import SourceError
from aptoro.output import to_json
from aptoro.schema import Schema, load_schema


def test_load_meta_success(tmp_path: Path, sample_schema_path: Path) -> None:
    """Test loading data with embedded metadata."""
    # Create a JSON file with metadata
    schema = load_schema(sample_schema_path)
    data = [
        {"id": "1", "lemma": "test", "pos": "noun"},
        {"id": "2", "lemma": "run", "pos": "verb"},
    ]

    # Manually construct the JSON content to ensure we test load_meta independently of to_json
    # (though integration tests will cover both)
    content = {"meta": schema.to_dict(), "data": data}

    json_path = tmp_path / "data_with_meta.json"
    with open(json_path, "w") as f:
        json.dump(content, f)

    # Test load_meta
    loaded_schema, loaded_data = load_meta(json_path)

    # Verify schema reconstruction
    assert isinstance(loaded_schema, Schema)
    assert loaded_schema.name == schema.name
    assert loaded_schema.description == schema.description
    assert loaded_schema.primary_key == schema.primary_key

    # Verify fields
    assert len(loaded_schema.fields) == len(schema.fields)
    assert loaded_schema.has_field("id")
    assert loaded_schema.has_field("lemma")

    # Verify data
    assert loaded_data == data


def test_load_meta_integration(tmp_path: Path, sample_schema_path: Path) -> None:
    """Test full cycle: to_json(include_meta=True) -> load_meta."""
    schema = load_schema(sample_schema_path)
    data = [
        {"id": "1", "lemma": "test", "pos": "noun"},
    ]

    # Export
    json_str = to_json(data, schema=schema, include_meta=True)
    json_path = tmp_path / "export.json"
    json_path.write_text(json_str)

    # Import
    loaded_schema, loaded_data = load_meta(json_path)

    # Verify
    assert loaded_schema.name == schema.name
    assert loaded_data == data


def test_load_meta_missing_file(tmp_path: Path) -> None:
    """Test error when file missing."""
    with pytest.raises(SourceError, match="Cannot read file"):
        load_meta(tmp_path / "nonexistent.json")


def test_load_meta_invalid_json(tmp_path: Path) -> None:
    """Test error when file is not valid JSON."""
    p = tmp_path / "invalid.json"
    p.write_text("{invalid json")

    with pytest.raises(SourceError, match="Invalid JSON"):
        load_meta(p)


def test_load_meta_missing_keys(tmp_path: Path) -> None:
    """Test error when required keys are missing."""
    p = tmp_path / "bad_structure.json"

    # Missing meta
    p.write_text('{"data": []}')
    with pytest.raises(SourceError, match="Missing 'meta' key"):
        load_meta(p)

    # Missing data
    p.write_text('{"meta": {}}')
    with pytest.raises(SourceError, match="Missing 'data' key"):
        load_meta(p)


def test_load_meta_invalid_types(tmp_path: Path) -> None:
    """Test error when keys have wrong types."""
    p = tmp_path / "bad_types.json"

    # meta is not dict
    p.write_text('{"meta": [], "data": []}')
    with pytest.raises(SourceError, match="'meta' must be an object"):
        load_meta(p)

    # data is not list
    p.write_text('{"meta": {}, "data": {}}')
    with pytest.raises(SourceError, match="'data' must be an array"):
        load_meta(p)
