"""Core type definitions for aptoro schemas.

This module defines the data structures used to represent schemas internally.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BaseType(Enum):
    """Supported base types for schema fields."""

    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"


@dataclass(frozen=True)
class FieldType:
    """Represents a parsed field type.

    Examples:
        str -> FieldType(base=STR)
        str? -> FieldType(base=STR, optional=True)
        str[a|b|c] -> FieldType(base=STR, constraints=('a', 'b', 'c'))
        int[1..10] -> FieldType(base=INT, min_value=1, max_value=10)
        list[str] -> FieldType(base=LIST, item_type=FieldType(base=STR))
    """

    base: BaseType
    optional: bool = False
    constraints: tuple[str, ...] | None = None  # For enum values like str[a|b|c]
    item_type: "FieldType | None" = None  # For list[T]
    default: Any = None
    has_default: bool = False
    min_value: int | float | None = None  # For int/float range constraints
    max_value: int | float | None = None  # For int/float range constraints

    def __str__(self) -> str:
        result = self.base.value
        if self.item_type:
            result = f"{result}[{self.item_type}]"
        elif self.min_value is not None or self.max_value is not None:
            min_str = str(self.min_value) if self.min_value is not None else ""
            max_str = str(self.max_value) if self.max_value is not None else ""
            result = f"{result}[{min_str}..{max_str}]"
        elif self.constraints:
            result = f"{result}[{'|'.join(self.constraints)}]"
        if self.optional:
            result = f"{result}?"
        if self.has_default:
            result = f"{result} = {self.default!r}"
        return result


@dataclass(frozen=True)
class Field:
    """Represents a single field in a schema."""

    name: str
    field_type: FieldType

    @property
    def is_optional(self) -> bool:
        """Check if field is optional (can be null/missing)."""
        return self.field_type.optional

    @property
    def is_required(self) -> bool:
        """Check if field is required."""
        return not self.field_type.optional and not self.field_type.has_default

    @property
    def has_default(self) -> bool:
        """Check if field has a default value."""
        return self.field_type.has_default

    @property
    def default(self) -> Any:
        """Get the default value."""
        return self.field_type.default


@dataclass(frozen=True)
class NestedField:
    """Represents a nested structure field.

    Used for complex fields like:
        senses:
          type: list
          items:
            definition: str
            examples: list[str]?
    """

    name: str
    is_list: bool
    fields: tuple["Field | NestedField", ...]
    optional: bool = False


@dataclass
class Schema:
    """Represents a complete schema definition.

    Attributes:
        name: Schema identifier
        description: Human-readable description
        version: Schema version string
        primary_key: Field name used as unique identifier (defaults to 'id')
        fields: Ordered collection of field definitions
        extends: List of parent schema paths for inheritance
    """

    name: str
    fields: tuple[Field | NestedField, ...]
    description: str | None = None
    version: str | None = None
    primary_key: str = "id"
    extends: tuple[str, ...] = field(default_factory=tuple)

    def get_field(self, name: str) -> Field | NestedField | None:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def has_field(self, name: str) -> bool:
        """Check if schema has a field with given name."""
        return self.get_field(name) is not None

    @property
    def required_fields(self) -> tuple[Field, ...]:
        """Get all required (non-optional, no default) fields."""
        return tuple(f for f in self.fields if isinstance(f, Field) and f.is_required)

    @property
    def optional_fields(self) -> tuple[Field, ...]:
        """Get all optional fields."""
        return tuple(f for f in self.fields if isinstance(f, Field) and f.is_optional)

    @property
    def field_names(self) -> tuple[str, ...]:
        """Get all field names."""
        return tuple(f.name for f in self.fields)

    def to_dict(self) -> dict[str, Any]:
        """Serialize schema to a dictionary suitable for JSON export.

        Returns:
            Dictionary with schema metadata and field definitions.
        """

        def _field_to_value(f: "Field | NestedField") -> str | dict[str, Any]:
            if isinstance(f, Field):
                return str(f.field_type)
            # NestedField
            return {
                "type": "list" if f.is_list else "dict",
                "optional": f.optional,
                "items": {nf.name: _field_to_value(nf) for nf in f.fields},
            }

        result: dict[str, Any] = {
            "schema_name": self.name,
            "fields": {f.name: _field_to_value(f) for f in self.fields},
        }

        if self.description:
            result["description"] = self.description
        if self.version:
            result["version"] = self.version
        if self.primary_key != "id":
            result["primary_key"] = self.primary_key

        return result
