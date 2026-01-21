"""Tests for Schema types and methods."""

from aptoro.schema.types import Field, Schema, BaseType
from aptoro.schema.parser import parse_type_string


def test_schema_to_dict_basic() -> None:
    """Test basic schema serialization."""
    fields = (
        Field(name="id", field_type=parse_type_string("str")),
        Field(name="count", field_type=parse_type_string("int")),
    )
    schema = Schema(name="test_schema", fields=fields, primary_key="id")

    data = schema.to_dict()

    assert data["schema_name"] == "test_schema"
    assert "fields" in data
    assert data["fields"]["id"] == "str"
    assert data["fields"]["count"] == "int"
    # "id" is default primary key, so it's omitted from output
    assert "primary_key" not in data


def test_schema_to_dict_full() -> None:
    """Test schema serialization with all options."""
    fields = (Field(name="id", field_type=parse_type_string("str")),)
    schema = Schema(
        name="full_schema",
        fields=fields,
        description="A test description",
        version="1.2.3",
        primary_key="uuid",
    )

    data = schema.to_dict()

    assert data["description"] == "A test description"
    assert data["version"] == "1.2.3"
    assert data["primary_key"] == "uuid"


def test_schema_to_dict_nested() -> None:
    """Test serialization of nested fields (if supported by serialization logic)."""
    # Note: NestedField support depends on implementation details of Schema.to_dict
    # Based on the implementation in src/aptoro/schema/types.py, it handles NestedField.
    # We need to construct a NestedField manually or parse one if parser supports it.
    # The parser currently seems to produce Field or NestedField?
    # Let's check Schema.to_dict implementation again. It checks isinstance(f, Field).
    # If it's NestedField, it recurses.

    # We can't easily construct NestedField from parse_type_string directly if it doesn't support complex syntax,
    # but we can import it.
    from aptoro.schema.types import NestedField

    sub_fields = (Field(name="sub", field_type=parse_type_string("int")),)
    nested = NestedField(name="nested", is_list=True, fields=sub_fields)

    schema = Schema(name="nested_schema", fields=(nested,))

    data = schema.to_dict()

    assert data["fields"]["nested"]["type"] == "list"
    assert data["fields"]["nested"]["items"]["sub"] == "int"
