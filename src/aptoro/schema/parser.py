"""Schema parsing from YAML files.

Handles the custom type syntax:
    str, int, float, bool    - basic types
    str?                     - optional type
    str = "default"          - type with default
    str[a|b|c]               - constrained/enum type
    list[str]                - list of type
    list[str]?               - optional list
    list[str] = []           - list with default
"""

import re
from pathlib import Path
from typing import Any

import yaml

from aptoro.errors import SchemaError
from aptoro.schema.types import BaseType, Field, FieldType, NestedField, Schema

# Regex patterns for type parsing
TYPE_PATTERN = re.compile(
    r"""
    ^
    (?P<base>str|int|float|bool|list|dict)  # Base type
    (?:\[(?P<inner>[^\]]+)\])?              # Optional inner type or constraints
    (?P<optional>\?)?                        # Optional marker
    (?:\s*=\s*(?P<default>.+))?             # Optional default value
    $
    """,
    re.VERBOSE,
)

CONSTRAINT_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\|[a-zA-Z_][a-zA-Z0-9_]*)*$")


def parse_type_string(type_str: str) -> FieldType:
    """Parse a type string into a FieldType.

    Args:
        type_str: Type specification like 'str', 'str?', 'str[a|b|c]', 'list[str]'

    Returns:
        Parsed FieldType

    Raises:
        SchemaError: If type string is invalid
    """
    type_str = type_str.strip()
    match = TYPE_PATTERN.match(type_str)

    if not match:
        raise SchemaError(f"Invalid type specification: {type_str!r}")

    base_str = match.group("base")
    inner = match.group("inner")
    optional = match.group("optional") is not None
    default_str = match.group("default")

    try:
        base = BaseType(base_str)
    except ValueError:
        raise SchemaError(f"Unknown base type: {base_str!r}")

    constraints: tuple[str, ...] | None = None
    item_type: FieldType | None = None

    if inner:
        if base == BaseType.LIST:
            # list[str] or list[int] etc.
            item_type = parse_type_string(inner)
        elif base == BaseType.STR:
            # str[a|b|c] - constraints
            if CONSTRAINT_PATTERN.match(inner):
                constraints = tuple(inner.split("|"))
            else:
                raise SchemaError(
                    f"Invalid constraint specification: {inner!r}. "
                    "Constraints must be pipe-separated identifiers."
                )
        else:
            raise SchemaError(f"Type {base_str} does not support inner type/constraints")

    # Parse default value
    default: Any = None
    has_default = False
    if default_str is not None:
        has_default = True
        default = _parse_default_value(default_str, base)

    return FieldType(
        base=base,
        optional=optional,
        constraints=constraints,
        item_type=item_type,
        default=default,
        has_default=has_default,
    )


def _parse_default_value(value_str: str, base_type: BaseType) -> Any:
    """Parse a default value string to its Python type."""
    value_str = value_str.strip()

    # Handle empty list
    if value_str == "[]":
        return []

    # Handle empty dict
    if value_str == "{}":
        return {}

    # Handle quoted strings
    if (value_str.startswith('"') and value_str.endswith('"')) or (
        value_str.startswith("'") and value_str.endswith("'")
    ):
        return value_str[1:-1]

    # Handle booleans
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False

    # Handle null/none
    if value_str.lower() in ("null", "none"):
        return None

    # Handle numbers
    if base_type == BaseType.INT:
        try:
            return int(value_str)
        except ValueError:
            raise SchemaError(f"Invalid integer default: {value_str!r}")
    if base_type == BaseType.FLOAT:
        try:
            return float(value_str)
        except ValueError:
            raise SchemaError(f"Invalid float default: {value_str!r}")

    # Default: treat as string
    return value_str


def _parse_field(name: str, value: Any) -> Field | NestedField:
    """Parse a field definition.

    Args:
        name: Field name
        value: Field value (type string or nested dict)

    Returns:
        Field or NestedField
    """
    if isinstance(value, str):
        # Simple field: name: type_string
        field_type = parse_type_string(value)
        return Field(name=name, field_type=field_type)

    if isinstance(value, dict):
        # Nested field definition
        if "type" in value and value.get("type") == "list" and "items" in value:
            # Nested list structure
            items = value["items"]
            if isinstance(items, dict):
                nested_fields = tuple(_parse_field(n, v) for n, v in items.items())
                return NestedField(
                    name=name,
                    is_list=True,
                    fields=nested_fields,
                    optional=value.get("optional", False),
                )

        raise SchemaError(
            f"Invalid nested field definition for {name!r}. "
            "Nested fields must have 'type: list' and 'items' keys."
        )

    raise SchemaError(
        f"Invalid field value for {name!r}: expected string or dict, got {type(value).__name__}"
    )


def parse_schema(data: dict[str, Any], base_path: Path | None = None) -> Schema:
    """Parse a schema from a dictionary (already loaded YAML).

    Args:
        data: Dictionary containing schema definition
        base_path: Base path for resolving 'extends' references

    Returns:
        Parsed Schema object

    Raises:
        SchemaError: If schema is invalid
    """
    if "name" not in data:
        raise SchemaError("Schema must have a 'name' field")

    if "fields" not in data:
        raise SchemaError("Schema must have a 'fields' section")

    name = data["name"]
    description = data.get("description")
    version = data.get("version")
    primary_key = data.get("primary_key", "id")

    # Handle inheritance
    extends_raw = data.get("extends", [])
    if isinstance(extends_raw, str):
        extends_raw = [extends_raw]
    extends = tuple(extends_raw)

    # Load parent schemas and merge fields
    inherited_fields: dict[str, Field | NestedField] = {}
    if extends and base_path:
        for parent_path in extends:
            parent_schema = load_schema(base_path / parent_path)
            for f in parent_schema.fields:
                inherited_fields[f.name] = f

    # Parse fields
    fields_data = data["fields"]
    if not isinstance(fields_data, dict):
        raise SchemaError("'fields' must be a mapping of field names to types")

    # Own fields override inherited
    own_fields: dict[str, Field | NestedField] = {}
    for field_name, field_value in fields_data.items():
        own_fields[field_name] = _parse_field(field_name, field_value)

    # Merge: inherited first, then own (own overrides)
    all_fields = {**inherited_fields, **own_fields}
    fields = tuple(all_fields.values())

    return Schema(
        name=name,
        fields=fields,
        description=description,
        version=version,
        primary_key=primary_key,
        extends=extends,
    )


def load_schema(path: str | Path) -> Schema:
    """Load a schema from a YAML file.

    Args:
        path: Path to the YAML schema file

    Returns:
        Parsed Schema object

    Raises:
        SchemaError: If file cannot be read or schema is invalid
    """
    path = Path(path)

    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SchemaError(f"Invalid YAML in schema file: {e}")
    except OSError as e:
        raise SchemaError(f"Cannot read schema file: {e}")

    if not isinstance(data, dict):
        raise SchemaError("Schema file must contain a YAML mapping")

    return parse_schema(data, base_path=path.parent)
