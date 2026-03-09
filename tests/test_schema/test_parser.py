"""Tests for schema parsing."""

from pathlib import Path

import pytest

from aptoro.errors import SchemaError
from aptoro.schema import load_schema
from aptoro.schema.parser import parse_type_string
from aptoro.schema.types import BaseType, Field


class TestParseTypeString:
    """Tests for parse_type_string function."""

    def test_basic_str(self) -> None:
        ft = parse_type_string("str")
        assert ft.base == BaseType.STR
        assert not ft.optional
        assert ft.constraints is None
        assert not ft.has_default

    def test_basic_int(self) -> None:
        ft = parse_type_string("int")
        assert ft.base == BaseType.INT
        assert not ft.optional

    def test_basic_float(self) -> None:
        ft = parse_type_string("float")
        assert ft.base == BaseType.FLOAT

    def test_basic_bool(self) -> None:
        ft = parse_type_string("bool")
        assert ft.base == BaseType.BOOL

    def test_special_types(self) -> None:
        for t, base in [
            ("url", BaseType.URL),
            ("file", BaseType.FILE),
            ("datetime", BaseType.DATETIME),
        ]:
            ft = parse_type_string(t)
            assert ft.base == base
            assert not ft.optional

    def test_optional_str(self) -> None:
        ft = parse_type_string("str?")
        assert ft.base == BaseType.STR
        assert ft.optional

    def test_optional_int(self) -> None:
        ft = parse_type_string("int?")
        assert ft.base == BaseType.INT
        assert ft.optional

    def test_optional_special_types(self) -> None:
        for t, base in [
            ("url?", BaseType.URL),
            ("file?", BaseType.FILE),
            ("datetime?", BaseType.DATETIME),
        ]:
            ft = parse_type_string(t)
            assert ft.base == base
            assert ft.optional

    def test_str_with_default(self) -> None:
        ft = parse_type_string('str = "hello"')
        assert ft.base == BaseType.STR
        assert ft.has_default
        assert ft.default == "hello"

    def test_int_with_default(self) -> None:
        ft = parse_type_string("int = 42")
        assert ft.base == BaseType.INT
        assert ft.has_default
        assert ft.default == 42

    def test_bool_with_default_true(self) -> None:
        ft = parse_type_string("bool = true")
        assert ft.base == BaseType.BOOL
        assert ft.has_default
        assert ft.default is True

    def test_bool_with_default_false(self) -> None:
        ft = parse_type_string("bool = false")
        assert ft.base == BaseType.BOOL
        assert ft.has_default
        assert ft.default is False

    def test_special_types_with_default(self) -> None:
        ft = parse_type_string('url = "https://example.com"')
        assert ft.base == BaseType.URL
        assert ft.has_default
        assert ft.default == "https://example.com"

        ft = parse_type_string('file = "path/to/file"')
        assert ft.base == BaseType.FILE
        assert ft.has_default
        assert ft.default == "path/to/file"

        ft = parse_type_string('datetime = "2023-01-01"')
        assert ft.base == BaseType.DATETIME
        assert ft.has_default
        assert ft.default == "2023-01-01"

    def test_str_with_constraints(self) -> None:
        ft = parse_type_string("str[noun|verb|adj]")
        assert ft.base == BaseType.STR
        assert ft.constraints == ("noun", "verb", "adj")

    def test_list_of_str(self) -> None:
        ft = parse_type_string("list[str]")
        assert ft.base == BaseType.LIST
        assert ft.item_type is not None
        assert ft.item_type.base == BaseType.STR

    def test_list_of_int(self) -> None:
        ft = parse_type_string("list[int]")
        assert ft.base == BaseType.LIST
        assert ft.item_type is not None
        assert ft.item_type.base == BaseType.INT

    def test_optional_list(self) -> None:
        ft = parse_type_string("list[str]?")
        assert ft.base == BaseType.LIST
        assert ft.optional
        assert ft.item_type is not None
        assert ft.item_type.base == BaseType.STR

    def test_list_with_default_empty(self) -> None:
        ft = parse_type_string("list[str] = []")
        assert ft.base == BaseType.LIST
        assert ft.has_default
        assert ft.default == []

    def test_invalid_type(self) -> None:
        with pytest.raises(SchemaError, match="Invalid type specification"):
            parse_type_string("invalid")

    def test_whitespace_handling(self) -> None:
        ft = parse_type_string("  str  ")
        assert ft.base == BaseType.STR

    def test_int_with_range_min_max(self) -> None:
        ft = parse_type_string("int[1..10]")
        assert ft.base == BaseType.INT
        assert ft.min_value == 1
        assert ft.max_value == 10

    def test_int_with_range_only_min(self) -> None:
        ft = parse_type_string("int[0..]")
        assert ft.base == BaseType.INT
        assert ft.min_value == 0
        assert ft.max_value is None

    def test_int_with_range_only_max(self) -> None:
        ft = parse_type_string("int[..100]")
        assert ft.base == BaseType.INT
        assert ft.min_value is None
        assert ft.max_value == 100

    def test_int_with_range_negative(self) -> None:
        ft = parse_type_string("int[-10..10]")
        assert ft.base == BaseType.INT
        assert ft.min_value == -10
        assert ft.max_value == 10

    def test_float_with_range_min_max(self) -> None:
        ft = parse_type_string("float[0.0..1.0]")
        assert ft.base == BaseType.FLOAT
        assert ft.min_value == 0.0
        assert ft.max_value == 1.0

    def test_float_with_range_only_min(self) -> None:
        ft = parse_type_string("float[0.5..]")
        assert ft.base == BaseType.FLOAT
        assert ft.min_value == 0.5
        assert ft.max_value is None

    def test_float_with_range_only_max(self) -> None:
        ft = parse_type_string("float[..3.14]")
        assert ft.base == BaseType.FLOAT
        assert ft.min_value is None
        assert ft.max_value == 3.14

    def test_float_with_range_negative(self) -> None:
        ft = parse_type_string("float[-273.15..0]")
        assert ft.base == BaseType.FLOAT
        assert ft.min_value == -273.15
        assert ft.max_value == 0

    def test_int_with_range_optional(self) -> None:
        ft = parse_type_string("int[1..10]?")
        assert ft.base == BaseType.INT
        assert ft.optional
        assert ft.min_value == 1
        assert ft.max_value == 10

    def test_int_with_range_and_default(self) -> None:
        ft = parse_type_string("int[1..10] = 5")
        assert ft.base == BaseType.INT
        assert ft.has_default
        assert ft.default == 5
        assert ft.min_value == 1
        assert ft.max_value == 10

    def test_invalid_range_no_dots(self) -> None:
        with pytest.raises(SchemaError, match="Invalid range specification"):
            parse_type_string("int[1-10]")

    def test_invalid_range_mixed_syntax(self) -> None:
        with pytest.raises(SchemaError, match="Invalid range specification"):
            parse_type_string("int[1|10]")

    def test_str_with_hyphenated_constraints(self) -> None:
        ft = parse_type_string("str[ritual|estrutura-central|designação-clânica]")
        assert ft.constraints == ("ritual", "estrutura-central", "designação-clânica")

    def test_str_with_accented_constraints(self) -> None:
        ft = parse_type_string("str[café|naïve|résumé]")
        assert ft.constraints == ("café", "naïve", "résumé")

    def test_str_with_spaces_in_constraints(self) -> None:
        ft = parse_type_string("str[hello world|foo bar]")
        assert ft.constraints == ("hello world", "foo bar")

    def test_str_empty_constraint_segment_raises(self) -> None:
        with pytest.raises(SchemaError, match="non-empty pipe-separated"):
            parse_type_string("str[a||b]")

    def test_str_leading_pipe_raises(self) -> None:
        with pytest.raises(SchemaError, match="non-empty pipe-separated"):
            parse_type_string("str[|a|b]")

    def test_str_with_regex_pattern(self) -> None:
        ft = parse_type_string("str[/^[a-z0-9-]+$/]")
        assert ft.base == BaseType.STR
        assert ft.pattern == "^[a-z0-9-]+$"
        assert ft.constraints is None

    def test_str_with_invalid_regex_raises(self) -> None:
        with pytest.raises(SchemaError, match="Invalid regex pattern"):
            parse_type_string("str[/(/]")

    def test_str_with_unbalanced_bracket_regex_raises(self) -> None:
        with pytest.raises(SchemaError):
            parse_type_string("str[/[unclosed/]")

    def test_str_regex_optional(self) -> None:
        ft = parse_type_string("str[/^[a-z]+$/]?")
        assert ft.pattern == "^[a-z]+$"
        assert ft.optional

    def test_str_regex_with_default(self) -> None:
        ft = parse_type_string('str[/^\\d{4}$/] = "0000"')
        assert ft.pattern == "^\\d{4}$"
        assert ft.has_default
        assert ft.default == "0000"

    def test_range_not_supported_for_str(self) -> None:
        # 1..10 is now treated as a valid constraint value (no longer errors)
        ft = parse_type_string("str[1..10]")
        assert ft.constraints == ("1..10",)


class TestLoadSchema:
    """Tests for load_schema function."""

    def test_load_simple_schema(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        assert schema.name == "lexicon_entry"
        assert schema.description == "Dictionary entries for testing"
        assert schema.version == "1.0"
        assert schema.primary_key == "id"

    def test_schema_has_fields(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        assert len(schema.fields) == 7
        assert schema.has_field("id")
        assert schema.has_field("lemma")
        assert schema.has_field("pos")

    def test_schema_field_types(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)

        id_field = schema.get_field("id")
        assert id_field is not None
        assert isinstance(id_field, Field)
        assert id_field.field_type.base == BaseType.STR
        assert id_field.is_required

        definition_pt = schema.get_field("definition_pt")
        assert definition_pt is not None
        assert isinstance(definition_pt, Field)
        assert definition_pt.is_optional

        frequency = schema.get_field("frequency")
        assert frequency is not None
        assert isinstance(frequency, Field)
        assert frequency.has_default
        assert frequency.default == 0

    def test_schema_with_constraints(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        pos = schema.get_field("pos")
        assert pos is not None
        assert isinstance(pos, Field)
        assert pos.field_type.constraints == ("noun", "verb", "adj", "adv")

    def test_schema_inheritance(self, child_schema_path: Path) -> None:
        schema = load_schema(child_schema_path)
        assert schema.name == "child_entry"
        # Should have inherited fields
        assert schema.has_field("id")
        assert schema.has_field("created_at")
        assert schema.has_field("updated_at")
        # Plus own fields
        assert schema.has_field("name")
        assert schema.has_field("value")

    def test_schema_not_found(self, fixtures_dir: Path) -> None:
        with pytest.raises(SchemaError, match="not found"):
            load_schema(fixtures_dir / "nonexistent.yaml")


class TestSchemaProperties:
    """Tests for Schema properties."""

    def test_required_fields(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        required = schema.required_fields
        required_names = [f.name for f in required]
        assert "id" in required_names
        assert "lemma" in required_names
        assert "definition_pt" not in required_names

    def test_optional_fields(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        optional = schema.optional_fields
        optional_names = [f.name for f in optional]
        assert "definition_pt" in optional_names
        assert "examples" in optional_names

    def test_field_names(self, sample_schema_path: Path) -> None:
        schema = load_schema(sample_schema_path)
        names = schema.field_names
        assert "id" in names
        assert "lemma" in names
        assert "pos" in names
