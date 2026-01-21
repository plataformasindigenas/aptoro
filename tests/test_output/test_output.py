"""Tests for output functions."""

import json
from pathlib import Path

import pytest

from aptoro import load, to_dicts, to_json
from aptoro.schema import load_schema


class TestToJson:
    """Tests for to_json function."""

    def test_to_json_basic(self, sample_schema_path: Path, sample_json_path: Path) -> None:
        records = load(str(sample_json_path), str(sample_schema_path))
        json_str = to_json(records)

        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_to_json_compact(self, sample_schema_path: Path, sample_json_path: Path) -> None:
        records = load(str(sample_json_path), str(sample_schema_path))
        json_str = to_json(records, indent=None)

        # Should be compact (no newlines in simple case)
        assert "\n" not in json_str or json_str.count("\n") == 0

    def test_to_json_preserves_data(self, sample_schema_path: Path, sample_json_path: Path) -> None:
        records = load(str(sample_json_path), str(sample_schema_path))
        json_str = to_json(records)
        data = json.loads(json_str)

        assert data[0]["lemma"] == "hello"
        assert data[1]["lemma"] == "run"


class TestToDicts:
    """Tests for to_dicts function."""

    def test_to_dicts_basic(self, sample_schema_path: Path, sample_json_path: Path) -> None:
        records = load(str(sample_json_path), str(sample_schema_path))
        dicts = to_dicts(records)

        assert isinstance(dicts, list)
        assert all(isinstance(d, dict) for d in dicts)
        assert len(dicts) == 2

    def test_to_dicts_preserves_data(
        self, sample_schema_path: Path, sample_json_path: Path
    ) -> None:
        records = load(str(sample_json_path), str(sample_schema_path))
        dicts = to_dicts(records)

        assert isinstance(dicts, list)
        assert dicts[0]["lemma"] == "hello"
        assert dicts[0]["pos"] == "noun"

    def test_to_dicts_with_meta(self, sample_schema_path: Path, sample_json_path: Path) -> None:
        """Test to_dicts with include_meta=True."""
        records = load(str(sample_json_path), str(sample_schema_path))
        schema = load_schema(sample_schema_path)

        result = to_dicts(records, schema=schema, include_meta=True)

        assert isinstance(result, dict)
        assert "meta" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2
        assert result["meta"]["schema_name"] == "lexicon_entry"

    def test_to_dicts_meta_requires_schema(
        self, sample_json_path: Path, sample_schema_path: Path
    ) -> None:
        """Test that schema is required when include_meta=True."""
        records = load(str(sample_json_path), str(sample_schema_path))

        with pytest.raises(ValueError, match="schema is required"):
            to_dicts(records, include_meta=True)
