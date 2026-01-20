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

    def test_optional_str(self) -> None:
        ft = parse_type_string("str?")
        assert ft.base == BaseType.STR
        assert ft.optional

    def test_optional_int(self) -> None:
        ft = parse_type_string("int?")
        assert ft.base == BaseType.INT
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
