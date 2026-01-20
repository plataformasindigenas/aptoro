"""Tests for data readers."""

from pathlib import Path

import pytest

from tabula.errors import SourceError
from tabula.readers import CSVReader, JSONReader, YAMLReader, read
from tabula.readers.base import detect_format


class TestDetectFormat:
    """Tests for format detection."""

    def test_csv_extension(self):
        assert detect_format("data.csv") == "csv"
        assert detect_format("https://example.com/data.csv") == "csv"

    def test_json_extension(self):
        assert detect_format("data.json") == "json"

    def test_yaml_extension(self):
        assert detect_format("data.yaml") == "yaml"
        assert detect_format("data.yml") == "yaml"

    def test_toml_extension(self):
        assert detect_format("data.toml") == "toml"

    def test_unknown_extension(self):
        with pytest.raises(SourceError, match="Cannot detect format"):
            detect_format("data.txt")

    def test_strips_query_params(self):
        assert detect_format("https://example.com/data.csv?token=abc") == "csv"


class TestCSVReader:
    """Tests for CSV reader."""

    def test_read_simple_csv(self):
        reader = CSVReader()
        content = "name,age\nAlice,30\nBob,25"
        records = reader.read(content)
        assert len(records) == 2
        assert records[0]["name"] == "Alice"
        assert records[0]["age"] == 30  # Type inferred

    def test_read_with_empty_values(self):
        reader = CSVReader()
        content = "name,age\nAlice,\nBob,25"
        records = reader.read(content)
        assert records[0]["age"] is None

    def test_read_without_type_inference(self):
        reader = CSVReader(infer_types=False)
        content = "name,age\nAlice,30"
        records = reader.read(content)
        assert records[0]["age"] == "30"  # Kept as string


class TestJSONReader:
    """Tests for JSON reader."""

    def test_read_array(self):
        reader = JSONReader()
        content = '[{"name": "Alice"}, {"name": "Bob"}]'
        records = reader.read(content)
        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_read_with_data_key(self):
        reader = JSONReader()
        content = '{"data": [{"name": "Alice"}]}'
        records = reader.read(content)
        assert len(records) == 1

    def test_read_with_custom_key(self):
        reader = JSONReader(data_key="items")
        content = '{"items": [{"name": "Alice"}]}'
        records = reader.read(content)
        assert len(records) == 1

    def test_invalid_json(self):
        reader = JSONReader()
        with pytest.raises(SourceError, match="JSON parsing error"):
            reader.read("not valid json")


class TestYAMLReader:
    """Tests for YAML reader."""

    def test_read_sequence(self):
        reader = YAMLReader()
        content = "- name: Alice\n- name: Bob"
        records = reader.read(content)
        assert len(records) == 2

    def test_read_with_data_key(self):
        reader = YAMLReader()
        content = "data:\n  - name: Alice"
        records = reader.read(content)
        assert len(records) == 1


class TestReadFunction:
    """Tests for the main read function."""

    def test_read_csv_file(self, sample_csv_path: Path):
        records = read(str(sample_csv_path))
        assert len(records) == 3
        assert records[0]["lemma"] == "hello"

    def test_read_json_file(self, sample_json_path: Path):
        records = read(str(sample_json_path))
        assert len(records) == 2
        assert records[0]["lemma"] == "hello"

    def test_read_with_explicit_format(self, sample_csv_path: Path):
        records = read(str(sample_csv_path), format="csv")
        assert len(records) == 3
