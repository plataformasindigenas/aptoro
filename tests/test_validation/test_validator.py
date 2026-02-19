"""Tests for validation."""

from pathlib import Path

import pytest

from aptoro.errors import ValidationError
from aptoro.schema import load_schema, parse_schema
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


class TestNullDefaults:
    """Tests for explicit null handling on fields with defaults."""

    def test_explicit_null_uses_int_default(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
                "frequency": None,
            }
        ]
        records = validate(data, schema)
        assert records[0].frequency == 0

    def test_explicit_null_uses_list_default(self) -> None:
        schema = parse_schema(
            {
                "name": "test_list_default",
                "fields": {
                    "id": "str",
                    "tags": "list[str] = []",
                },
            }
        )
        data = [{"id": "1", "tags": None}]
        records = validate(data, schema)
        assert records[0].tags == []

    def test_explicit_null_optional_stays_none(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": "hello",
                "pos": "noun",
                "definition": "a greeting",
                "definition_pt": None,
            }
        ]
        records = validate(data, schema)
        assert records[0].definition_pt is None

    def test_explicit_null_required_fails(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        data = [
            {
                "id": "1",
                "lemma": None,
                "pos": "noun",
                "definition": "a greeting",
            }
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate(data, schema)
        assert "lemma" in str(exc_info.value)


class TestValidationErrorSummary:
    """Tests for ValidationError.summary() method."""

    def _make_error(self, n: int) -> ValidationError:
        """Create a ValidationError with n FieldErrors."""
        err = ValidationError(source="test.csv", schema_name="test_schema")
        for i in range(n):
            err.add_error(
                field=f"field_{i}",
                expected="str",
                got=str(i),
                row=i + 1,
            )
        return err

    def test_summary_fewer_than_max(self):
        err = self._make_error(3)
        text = err.summary(max_errors=10)
        assert "3 error(s)" in text
        assert "field_0" in text
        assert "field_1" in text
        assert "field_2" in text
        assert "more error" not in text

    def test_summary_exactly_max(self):
        err = self._make_error(5)
        text = err.summary(max_errors=5)
        assert "5 error(s)" in text
        assert "field_4" in text
        assert "more error" not in text

    def test_summary_more_than_max(self):
        err = self._make_error(15)
        text = err.summary(max_errors=10)
        assert "15 error(s)" in text
        # First 10 shown
        assert "field_0" in text
        assert "field_9" in text
        # 11th not shown
        assert "field_10" not in text
        assert "... and 5 more error(s)" in text

    def test_summary_default_max_is_10(self):
        err = self._make_error(12)
        text = err.summary()
        assert "field_9" in text
        assert "field_10" not in text
        assert "... and 2 more error(s)" in text

    def test_summary_includes_source_and_schema(self):
        err = self._make_error(1)
        text = err.summary()
        assert "Source: test.csv" in text
        assert "Schema: test_schema" in text

    def test_summary_max_errors_one(self):
        err = self._make_error(3)
        text = err.summary(max_errors=1)
        assert "field_0" in text
        assert "field_1" not in text
        assert "... and 2 more error(s)" in text
