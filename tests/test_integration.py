"""Integration tests for aptoro."""

from pathlib import Path

import pytest

from aptoro import load, load_schema, read, to_dicts, to_json, validate


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_load_csv_and_validate(self, sample_schema_path: Path, sample_csv_path: Path):
        """Test the full pipeline with CSV data."""
        records = load(str(sample_csv_path), str(sample_schema_path))

        assert len(records) == 3
        assert records[0].lemma == "hello"
        assert records[0].pos == "noun"
        assert records[1].lemma == "run"
        assert records[1].pos == "verb"
        assert records[2].lemma == "big"
        assert records[2].pos == "adj"

    def test_load_json_and_validate(self, sample_schema_path: Path, sample_json_path: Path):
        """Test the full pipeline with JSON data."""
        records = load(str(sample_json_path), str(sample_schema_path))

        assert len(records) == 2
        assert records[0].lemma == "hello"
        assert records[1].examples == ["I run every day", "She runs fast"]

    def test_step_by_step_pipeline(self, sample_schema_path: Path, sample_csv_path: Path):
        """Test using individual functions."""
        # Step 1: Load schema
        schema = load_schema(sample_schema_path)
        assert schema.name == "lexicon_entry"

        # Step 2: Read data
        data = read(str(sample_csv_path))
        assert len(data) == 3

        # Step 3: Validate
        records = validate(data, schema)
        assert len(records) == 3

        # Step 4: Export
        json_str = to_json(records)
        assert "hello" in json_str

        dicts = to_dicts(records)
        assert dicts[0]["lemma"] == "hello"

    def test_schema_with_inheritance(self, child_schema_path: Path):
        """Test that schema inheritance works correctly."""
        schema = load_schema(child_schema_path)

        # Should have inherited fields
        assert schema.has_field("id")
        assert schema.has_field("created_at")

        # And own fields
        assert schema.has_field("name")
        assert schema.has_field("value")

        # Validate data
        data = [
            {
                "id": "1",
                "name": "test",
                "value": 42,
            }
        ]
        records = validate(data, schema)
        assert records[0].id == "1"
        assert records[0].name == "test"
        assert records[0].value == 42
        # Optional inherited field should be None
        assert records[0].created_at is None


class TestRealWorldScenarios:
    """Tests simulating real-world usage patterns."""

    def test_linguistic_dictionary_entry(self, fixtures_dir: Path):
        """Test with realistic linguistic dictionary data."""
        # Create a more complex schema inline
        schema_content = """
name: bororo_entry
description: Bororo dictionary entry

fields:
  id: str
  lemma: str
  pos: str[noun|verb|adj|adv|particle]
  gloss_pt: str
  gloss_en: str?
  phonetic: str?
  examples: list[str]?
  semantic_domain: str?
  notes: str?
"""
        schema_path = fixtures_dir / "bororo_schema.yaml"
        schema_path.write_text(schema_content)

        try:
            schema = load_schema(schema_path)

            data = [
                {
                    "id": "boe001",
                    "lemma": "boe",
                    "pos": "noun",
                    "gloss_pt": "gente, pessoa",
                    "gloss_en": "person, people",
                    "phonetic": "[ˈbɔe]",
                    "examples": ["Boe modo", "Boe eno"],
                    "semantic_domain": "human",
                },
                {
                    "id": "boe002",
                    "lemma": "eno",
                    "pos": "noun",
                    "gloss_pt": "língua, idioma",
                    "semantic_domain": "language",
                },
            ]

            records = validate(data, schema)
            assert len(records) == 2
            assert records[0].lemma == "boe"
            assert records[0].examples == ["Boe modo", "Boe eno"]
            assert records[1].gloss_en is None  # Optional field

        finally:
            schema_path.unlink()
