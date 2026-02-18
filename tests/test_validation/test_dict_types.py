"""Tests for dict and object type support."""

import pytest

from aptoro.errors import SchemaError, ValidationError
from aptoro.schema import load_schema
from aptoro.schema.parser import parse_type_string
from aptoro.schema.types import BaseType, Field, NestedField
from aptoro.validation import validate

# ---------------------------------------------------------------------------
# Parser tests: dict types
# ---------------------------------------------------------------------------


class TestParseDictTypes:
    """Tests for parsing dict type strings."""

    def test_dict_basic(self) -> None:
        ft = parse_type_string("dict")
        assert ft.base == BaseType.DICT
        assert not ft.optional
        assert ft.value_type is None

    def test_dict_optional(self) -> None:
        ft = parse_type_string("dict?")
        assert ft.base == BaseType.DICT
        assert ft.optional
        assert ft.value_type is None

    def test_dict_default_empty(self) -> None:
        ft = parse_type_string("dict = {}")
        assert ft.base == BaseType.DICT
        assert ft.has_default
        assert ft.default == {}

    def test_dict_str_str(self) -> None:
        ft = parse_type_string("dict[str, str]")
        assert ft.base == BaseType.DICT
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.STR

    def test_dict_str_int(self) -> None:
        ft = parse_type_string("dict[str, int]")
        assert ft.base == BaseType.DICT
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.INT

    def test_dict_str_float(self) -> None:
        ft = parse_type_string("dict[str, float]")
        assert ft.base == BaseType.DICT
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.FLOAT

    def test_dict_str_bool(self) -> None:
        ft = parse_type_string("dict[str, bool]")
        assert ft.base == BaseType.DICT
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.BOOL

    def test_dict_typed_optional(self) -> None:
        ft = parse_type_string("dict[str, str]?")
        assert ft.base == BaseType.DICT
        assert ft.optional
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.STR

    def test_dict_typed_with_default(self) -> None:
        ft = parse_type_string("dict[str, int] = {}")
        assert ft.base == BaseType.DICT
        assert ft.has_default
        assert ft.default == {}
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.INT

    def test_dict_int_key_raises(self) -> None:
        with pytest.raises(SchemaError, match="dict keys must be 'str'"):
            parse_type_string("dict[int, str]")

    def test_dict_str_shorthand(self) -> None:
        ft = parse_type_string("dict[str]")
        assert ft.base == BaseType.DICT
        assert ft.value_type is not None
        assert ft.value_type.base == BaseType.STR

    def test_dict_str_rendering(self) -> None:
        ft = parse_type_string("dict[str, int]")
        assert str(ft) == "dict[str, int]"

    def test_dict_str_rendering_optional(self) -> None:
        ft = parse_type_string("dict[str, str]?")
        assert str(ft) == "dict[str, str]?"


# ---------------------------------------------------------------------------
# Parser tests: object type
# ---------------------------------------------------------------------------


class TestParseObjectType:
    """Tests for parsing object type strings."""

    def test_object_basic(self) -> None:
        ft = parse_type_string("object")
        assert ft.base == BaseType.OBJECT
        assert not ft.optional

    def test_object_optional(self) -> None:
        ft = parse_type_string("object?")
        assert ft.base == BaseType.OBJECT
        assert ft.optional

    def test_object_block_parsing(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        infobox = schema.get_field("infobox")
        assert infobox is not None
        assert isinstance(infobox, NestedField)
        assert not infobox.is_list
        assert infobox.optional
        assert len(infobox.fields) == 3

    def test_object_block_required(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        stats = schema.get_field("stats")
        assert stats is not None
        assert isinstance(stats, NestedField)
        assert not stats.is_list
        assert not stats.optional
        assert len(stats.fields) == 2

    def test_object_nested_field_types(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        stats = schema.get_field("stats")
        assert isinstance(stats, NestedField)
        count_field = next(f for f in stats.fields if f.name == "count")
        assert isinstance(count_field, Field)
        assert count_field.field_type.base == BaseType.INT

        label_field = next(f for f in stats.fields if f.name == "label")
        assert isinstance(label_field, Field)
        assert label_field.field_type.base == BaseType.STR
        assert label_field.has_default
        assert label_field.default == "default"


# ---------------------------------------------------------------------------
# Validation tests: dict passthrough
# ---------------------------------------------------------------------------


class TestDictValidation:
    """Tests for dict type validation."""

    def test_dict_passthrough(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [
            {
                "id": "1",
                "metadata": {"key": "value", "nested": [1, 2, 3]},
            }
        ]
        records = validate(data, schema)
        assert records[0].metadata == {"key": "value", "nested": [1, 2, 3]}

    def test_dict_optional_missing(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [{"id": "1"}]
        records = validate(data, schema)
        assert records[0].metadata is None
        assert records[0].tags is None

    def test_dict_optional_none(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [{"id": "1", "metadata": None}]
        records = validate(data, schema)
        assert records[0].metadata is None

    def test_dict_default_value(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [{"id": "1"}]
        records = validate(data, schema)
        assert records[0].scores == {}

    def test_typed_dict_valid(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [
            {
                "id": "1",
                "tags": {"color": "blue", "size": "large"},
            }
        ]
        records = validate(data, schema)
        assert records[0].tags == {"color": "blue", "size": "large"}

    def test_typed_dict_wrong_value_type(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [
            {
                "id": "1",
                "scores": {"math": "not_an_int"},  # should be int
            }
        ]
        with pytest.raises(ValidationError):
            validate(data, schema)

    def test_typed_dict_int_values(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [
            {
                "id": "1",
                "scores": {"math": 95, "science": 87},
            }
        ]
        records = validate(data, schema)
        assert records[0].scores == {"math": 95, "science": 87}

    def test_dict_not_a_dict_fails(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        data = [
            {
                "id": "1",
                "metadata": "not a dict",
            }
        ]
        with pytest.raises(ValidationError):
            validate(data, schema)


# ---------------------------------------------------------------------------
# Validation tests: object type
# ---------------------------------------------------------------------------


class TestObjectValidation:
    """Tests for object type validation."""

    def test_object_valid_data(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "stats": {"count": 10, "label": "test"},
            }
        ]
        records = validate(data, schema)
        assert records[0].stats == {"count": 10, "label": "test"}

    def test_object_with_defaults(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "stats": {"count": 5},
            }
        ]
        records = validate(data, schema)
        assert records[0].stats["count"] == 5
        assert records[0].stats["label"] == "default"

    def test_object_missing_required_nested_field(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "stats": {"label": "test"},  # missing required "count"
            }
        ]
        with pytest.raises(ValidationError):
            validate(data, schema)

    def test_object_optional_none(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "stats": {"count": 1},
            }
        ]
        records = validate(data, schema)
        assert records[0].infobox is None

    def test_object_optional_with_data(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "infobox": {
                    "nome_científico": "Panthera onca",
                    "família": "Felidae",
                    "habitat": "Tropical forests",
                },
                "stats": {"count": 1},
            }
        ]
        records = validate(data, schema)
        assert records[0].infobox["nome_científico"] == "Panthera onca"

    def test_object_optional_nested_fields(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                "infobox": {"nome_científico": "Panthera onca"},
                "stats": {"count": 1},
            }
        ]
        records = validate(data, schema)
        assert records[0].infobox["nome_científico"] == "Panthera onca"
        assert records[0].infobox["família"] is None

    def test_object_missing_required_top_level(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        data = [
            {
                "id": "1",
                # missing required "stats"
            }
        ]
        with pytest.raises(ValidationError):
            validate(data, schema)


# ---------------------------------------------------------------------------
# Schema serialization tests
# ---------------------------------------------------------------------------


class TestDictObjectSerialization:
    """Tests for to_dict serialization."""

    def test_object_to_dict(self) -> None:
        schema = load_schema("tests/fixtures/object_schema.yaml")
        d = schema.to_dict()
        infobox = d["fields"]["infobox"]
        assert infobox["type"] == "object"
        assert infobox["optional"] is True
        assert "fields" in infobox
        assert "nome_científico" in infobox["fields"]

    def test_dict_field_to_dict(self) -> None:
        schema = load_schema("tests/fixtures/dict_schema.yaml")
        d = schema.to_dict()
        assert d["fields"]["metadata"] == "dict?"
        assert d["fields"]["tags"] == "dict[str, str]?"
