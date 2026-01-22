"""Tests for validation."""

from pathlib import Path

import pytest

from aptoro.errors import ValidationError
from aptoro.schema import load_schema
from aptoro.validation import validate


class TestValidation:
    """Tests for the validate function."""

    def test_validate_valid_data(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        records = validate(data, schema)
        assert len(records) == 1
        assert records[0].id == "1"
        assert records[0].lemma == "hello"
        assert records[0].pos == "noun"

    def test_validate_with_optional_fields(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
                "definition_pt": "uma saudação",
            }
        ]
        records = validate(data, schema)
        assert records[0].definition_pt == "uma saudação"

    def test_validate_with_default_values(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        records = validate(data, schema)
        # frequency has default of 0
        assert records[0].frequency == 0

    def test_validate_missing_required_field(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                # Missing "lemma"
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "lemma" in str(exc_info.value)

    def test_validate_invalid_enum_value(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "invalid_pos",  # Not in [noun|verb|adj|adv]
                "definition": "a greeting",
            }
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "pos" in str(exc_info.value)

    def test_validate_collect_errors(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {"id": "1"},  # Missing multiple required fields
            {"id": "2", "lemma": "test", "pos": "invalid", "definition": "test"},
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema, collect_errors=True)
        # Should have collected multiple errors
        assert len(exc_info.value.errors) > 1

    def test_validate_list_field(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "run",
                "pos": "verb",
                "definition": "to move quickly",
                "examples": ["I run fast", "She runs daily"],
            }
        ]
        records = validate(data, schema)
        assert records[0].examples == ["I run fast", "She runs daily"]


class TestDataclassGeneration:
    """Tests for dataclass generation from schemas."""

    def test_generated_dataclass_is_frozen(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        records = validate(data, schema)

        # Should be immutable
        with pytest.raises(AttributeError):
            records[0].lemma = "changed"

    def test_generated_dataclass_has_correct_fields(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        records = validate(data, schema)

        # Should have all schema fields as attributes
        assert hasattr(records[0], "id")
        assert hasattr(records[0], "lemma")
        assert hasattr(records[0], "pos")
        assert hasattr(records[0], "definition")
        assert hasattr(records[0], "definition_pt")
        assert hasattr(records[0], "examples")
        assert hasattr(records[0], "frequency")


class TestRangeConstraints:
    """Tests for int/float range constraints validation."""

    def test_validate_int_within_range(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 5, "score": 0.5},
        ]
        records = validate(data, schema)
        assert records[0].count == 5
        assert records[0].score == 0.5

    def test_validate_int_below_min(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 0, "score": 0.5},  # count < 1
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "count" in str(exc_info.value)

    def test_validate_int_above_max(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 11, "score": 0.5},  # count > 10
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "count" in str(exc_info.value)

    def test_validate_float_below_min(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 5, "score": -0.1},  # score < 0.0
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "score" in str(exc_info.value)

    def test_validate_float_above_max(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 5, "score": 1.5},  # score > 1.0
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "score" in str(exc_info.value)

    def test_validate_int_only_min_constraint(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 5, "score": 0.5, "value": 100},  # value >= 0
        ]
        records = validate(data, schema)
        assert records[0].value == 100

    def test_validate_int_only_max_constraint(self) -> None:
        from aptoro.schema import load_schema
        from aptoro.validation import validate

        schema = load_schema("tests/fixtures/range_schema.yaml")
        data = [
            {"id": "1", "count": 5, "score": 0.5, "limit": 50},  # limit <= 100
        ]
        records = validate(data, schema)
        assert records[0].limit == 50
