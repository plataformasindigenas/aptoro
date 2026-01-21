"""Functions for loading JSON with embedded schema metadata."""

import json
from pathlib import Path
from typing import Any

from aptoro.errors import SourceError
from aptoro.schema.parser import parse_type_string
from aptoro.schema.types import Field, NestedField, Schema


def load_meta(source: str | Path) -> tuple[Schema, list[dict[str, Any]]]:
    """Load JSON file with embedded aptoro metadata.

    Reads a JSON file that was exported with include_meta=True and
    reconstructs the schema from the embedded metadata.

    Args:
        source: Path to JSON file with metadata

    Returns:
        Tuple of (Schema, raw_data) where:
        - Schema: Reconstructed schema object
        - raw_data: List of record dictionaries

    Raises:
        SourceError: If file cannot be read or has invalid format

    Example:
        >>> schema, data = load_meta("fauna_with_meta.json")
        >>> records = validate(data, schema)  # Get typed dataclasses
    """
    path = Path(source)

    try:
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
    except OSError as e:
        raise SourceError(f"Cannot read file: {e}") from e
    except json.JSONDecodeError as e:
        raise SourceError(f"Invalid JSON: {e}") from e

    if not isinstance(content, dict):
        raise SourceError("Expected JSON object with 'meta' and 'data' keys")

    if "meta" not in content:
        raise SourceError("Missing 'meta' key in JSON")

    if "data" not in content:
        raise SourceError("Missing 'data' key in JSON")

    meta = content["meta"]
    data = content["data"]

    if not isinstance(meta, dict):
        raise SourceError("'meta' must be an object")

    if not isinstance(data, list):
        raise SourceError("'data' must be an array")

    schema = _schema_from_meta(meta)
    return schema, data


def _schema_from_meta(meta: dict[str, Any]) -> Schema:
    """Reconstruct a Schema from metadata dictionary.

    Args:
        meta: Metadata dictionary with schema_name, fields, etc.

    Returns:
        Reconstructed Schema object

    Raises:
        SourceError: If metadata is invalid
    """
    if "schema_name" not in meta:
        raise SourceError("Missing 'schema_name' in metadata")

    if "fields" not in meta:
        raise SourceError("Missing 'fields' in metadata")

    name = meta["schema_name"]
    fields_data = meta["fields"]

    if not isinstance(fields_data, dict):
        raise SourceError("'fields' must be an object")

    fields: list[Field | NestedField] = []
    for field_name, field_value in fields_data.items():
        fields.append(_parse_field_from_meta(field_name, field_value))

    return Schema(
        name=name,
        fields=tuple(fields),
        description=meta.get("description"),
        version=meta.get("version"),
        primary_key=meta.get("primary_key", "id"),
    )


def _parse_field_from_meta(name: str, value: str | dict[str, Any]) -> Field | NestedField:
    """Parse a field from metadata.

    Args:
        name: Field name
        value: Type string or nested field definition

    Returns:
        Field or NestedField object
    """
    if isinstance(value, str):
        field_type = parse_type_string(value)
        return Field(name=name, field_type=field_type)

    if isinstance(value, dict):
        # Nested field
        is_list = value.get("type") == "list"
        optional = value.get("optional", False)
        items = value.get("items", {})

        nested_fields = tuple(
            _parse_field_from_meta(n, v) for n, v in items.items()
        )

        return NestedField(
            name=name,
            is_list=is_list,
            fields=nested_fields,
            optional=optional,
        )

    raise SourceError(f"Invalid field value for {name!r}: expected string or object")
