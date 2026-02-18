"""Dynamic dataclass generation from schemas."""

from dataclasses import field as dataclass_field
from dataclasses import make_dataclass
from typing import Any, get_type_hints

from aptoro.schema.types import BaseType, Field, FieldType, NestedField, Schema


def _python_type_for_field_type(field_type: FieldType) -> type:
    """Convert FieldType to Python type annotation."""
    base_map: dict[BaseType, type] = {
        BaseType.STR: str,
        BaseType.INT: int,
        BaseType.FLOAT: float,
        BaseType.BOOL: bool,
        BaseType.DICT: dict,
        BaseType.URL: str,
        BaseType.FILE: str,
        BaseType.DATETIME: str,
    }

    if field_type.base == BaseType.LIST:
        if field_type.item_type:
            item_type = _python_type_for_field_type(field_type.item_type)
            python_type: type = list[item_type]  # type: ignore
        else:
            python_type = list
    elif field_type.base == BaseType.DICT:
        if field_type.value_type:
            val_type = _python_type_for_field_type(field_type.value_type)
            python_type = dict[str, val_type]  # type: ignore
        else:
            python_type = dict
    elif field_type.base == BaseType.OBJECT:
        python_type = dict
    else:
        python_type = base_map.get(field_type.base, Any)

    # Wrap in Optional if field is optional
    if field_type.optional:
        python_type = python_type | None  # type: ignore

    return python_type


def _make_field_spec(f: Field) -> tuple[str, type, Any]:
    """Create a dataclass field specification.

    Returns:
        Tuple of (name, type, field_default_or_field_object)
    """
    python_type = _python_type_for_field_type(f.field_type)

    if f.has_default:
        default = f.default
        # Mutable defaults need field(default_factory=...)
        if isinstance(default, (list, dict)):

            def factory(d=default):  # type: ignore
                return d.copy()

            return (
                f.name,
                python_type,
                dataclass_field(default_factory=factory),
            )
        return (f.name, python_type, default)
    elif f.is_optional:
        return (f.name, python_type, None)
    else:
        # Required field - no default
        return (f.name, python_type, dataclass_field())


def generate_dataclass(schema: Schema) -> type:
    """Generate a dataclass type from a schema.

    Args:
        schema: Schema to generate dataclass from

    Returns:
        A new dataclass type with fields matching the schema

    Example:
        >>> schema = load_schema("lexicon.yaml")
        >>> LexiconEntry = generate_dataclass(schema)
        >>> entry = LexiconEntry(id="1", lemma="hello")
    """
    fields_spec: list[tuple[str, type] | tuple[str, type, Any]] = []

    # Sort fields: required first (no default), then optional/defaulted
    required_fields = []
    optional_fields = []

    required_nested: list[NestedField] = []
    optional_nested: list[NestedField] = []

    for f in schema.fields:
        if isinstance(f, Field):
            if f.is_required:
                required_fields.append(f)
            else:
                optional_fields.append(f)
        elif isinstance(f, NestedField):
            if f.optional:
                optional_nested.append(f)
            else:
                required_nested.append(f)

    # Build field specs in correct order (required first, then optional)
    for f in required_fields:
        fields_spec.append(_make_field_spec(f))

    for nf in required_nested:
        if nf.is_list:
            python_type: type = list[dict]  # type: ignore
        else:
            python_type = dict
        fields_spec.append((nf.name, python_type, dataclass_field()))

    for f in optional_fields:
        fields_spec.append(_make_field_spec(f))

    for nf in optional_nested:
        if nf.is_list:
            python_type = list[dict] | None  # type: ignore
        else:
            python_type = dict | None  # type: ignore
        fields_spec.append((nf.name, python_type, None))

    # Create class name from schema name (PascalCase)
    class_name = "".join(word.capitalize() for word in schema.name.split("_"))

    # Generate the dataclass
    return make_dataclass(
        class_name,
        fields_spec,
        frozen=True,  # Immutable by default
    )


def create_instance(dataclass_type: type, data: dict[str, Any]) -> Any:
    """Create a dataclass instance from a dictionary.

    Args:
        dataclass_type: The dataclass type (from generate_dataclass)
        data: Dictionary of field values

    Returns:
        Instance of the dataclass
    """
    # Filter data to only include fields that exist in the dataclass
    hints = get_type_hints(dataclass_type)
    filtered_data = {k: v for k, v in data.items() if k in hints}
    return dataclass_type(**filtered_data)
