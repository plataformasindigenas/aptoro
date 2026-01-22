"""Data validation against schemas using Pydantic."""

import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, create_model
from pydantic import ValidationError as PydanticValidationError
from pydantic.fields import FieldInfo

from aptoro.errors import FieldError, ValidationError
from aptoro.schema.types import BaseType, Field, FieldType, Schema
from aptoro.validation.dataclass_gen import create_instance, generate_dataclass


def validate_url(value: str) -> str:
    """Validate that a URL is accessible."""
    try:
        req = urllib.request.Request(value, headers={"User-Agent": "Aptoro/0.2.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status >= 400:
                raise ValueError(f"URL returned status {response.status}")
    except (urllib.error.URLError, ValueError) as e:
        raise ValueError(f"URL validation failed: {e}") from e
    return value


def validate_file(value: str) -> str:
    """Validate that a file exists."""
    path = Path(value)
    if not path.is_file():
        raise ValueError(f"File not found: {value}")
    return value


def validate_datetime(value: str) -> str:
    """Validate that a string is a valid ISO 8601 datetime/date.

    Ensures the result is UTC.
    """
    try:
        # Try full datetime first
        dt = datetime.fromisoformat(value)
    except ValueError:
        # Check if it's just a date
        try:
            d = datetime.strptime(value, "%Y-%m-%d").date()
            dt = datetime.combine(d, datetime.min.time())
        except ValueError as e:
            raise ValueError(
                f"Invalid datetime format: {value}. Expected ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
            ) from e

    # Ensure timezone awareness (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Return normalized ISO format
    return dt.isoformat()


def _pydantic_type_for_field_type(field_type: FieldType) -> type:
    """Convert FieldType to Pydantic-compatible type."""
    from typing import Literal

    base_map: dict[BaseType, type] = {
        BaseType.STR: str,
        BaseType.INT: int,
        BaseType.FLOAT: float,
        BaseType.BOOL: bool,
        BaseType.DICT: dict,
    }

    if field_type.base == BaseType.URL:
        python_type = Annotated[str, AfterValidator(validate_url)]  # type: ignore
    elif field_type.base == BaseType.FILE:
        python_type = Annotated[str, AfterValidator(validate_file)]  # type: ignore
    elif field_type.base == BaseType.DATETIME:
        python_type = Annotated[str, AfterValidator(validate_datetime)]  # type: ignore
    elif field_type.base == BaseType.STR and field_type.constraints:
        # Create Literal type for enum values
        python_type = Literal[field_type.constraints]  # type: ignore
    elif field_type.base == BaseType.INT or field_type.base == BaseType.FLOAT:
        # Handle int/float with range constraints - just return the base type
        # Range constraints are handled in _create_pydantic_model via Field()
        python_type = base_map[field_type.base]
    elif field_type.base == BaseType.LIST:
        if field_type.item_type:
            item_type = _pydantic_type_for_field_type(field_type.item_type)
            python_type = list[item_type]  # type: ignore
        else:
            python_type = list
    else:
        python_type = base_map.get(field_type.base, Any)

    # Wrap in Optional if field is optional
    if field_type.optional:
        python_type = python_type | None  # type: ignore

    return python_type


def _create_pydantic_model(schema: Schema) -> type[BaseModel]:
    """Create a Pydantic model from a schema for validation."""
    from pydantic import Field as PydanticField

    field_definitions: dict[str, tuple[type, FieldInfo]] = {}

    for f in schema.fields:
        if isinstance(f, Field):
            python_type = _pydantic_type_for_field_type(f.field_type)

            # Handle range constraints for int/float
            if (f.field_type.base == BaseType.INT or f.field_type.base == BaseType.FLOAT) and (
                f.field_type.min_value is not None or f.field_type.max_value is not None
            ):
                field_info_kwargs: dict[str, int | float] = {}
                if f.field_type.min_value is not None:
                    field_info_kwargs["ge"] = f.field_type.min_value
                if f.field_type.max_value is not None:
                    field_info_kwargs["le"] = f.field_type.max_value
                if f.has_default:
                    field_info_kwargs["default"] = f.default
                    field_info_kwargs["validate_default"] = True
                field_info = PydanticField(**field_info_kwargs)  # type: ignore
            elif f.has_default:
                field_info = FieldInfo(default=f.default, validate_default=True)
            elif f.is_optional:
                field_info = FieldInfo(default=None)
            else:
                field_info = FieldInfo()

            field_definitions[f.name] = (python_type, field_info)

    # Create model class name
    model_name = "".join(word.capitalize() for word in schema.name.split("_")) + "Model"

    return create_model(  # type: ignore
        model_name,
        __config__=ConfigDict(strict=False, extra="ignore", coerce_numbers_to_str=True),
        **field_definitions,
    )


def _convert_pydantic_error(
    error: dict[str, Any],
    row_index: int | None = None,
) -> FieldError:
    """Convert a Pydantic validation error to our FieldError format."""
    loc = error.get("loc", ())
    field_name = str(loc[0]) if loc else "unknown"
    error_type = error.get("type", "unknown")
    msg = error.get("msg", "validation error")
    input_value = error.get("input")

    # Build expected description based on error type
    if error_type == "literal_error":
        ctx = error.get("ctx", {})
        expected_values = ctx.get("expected", "")
        expected = f"one of [{expected_values}]"
    elif error_type == "missing":
        expected = "required field"
    elif error_type == "string_type":
        expected = "str"
    elif error_type == "int_type":
        expected = "int"
    elif error_type == "float_type":
        expected = "float"
    elif error_type == "bool_type":
        expected = "bool"
    elif error_type == "list_type":
        expected = "list"
    else:
        expected = msg

    return FieldError(
        field=field_name,
        expected=expected,
        got=str(input_value) if input_value is not None else "null/missing",
        row=row_index,
        column=field_name,
    )


def validate(
    data: list[dict[str, Any]],
    schema: Schema,
    *,
    collect_errors: bool = False,
    source: str | None = None,
) -> list[Any]:
    """Validate data against a schema and return typed dataclass instances.

    Args:
        data: List of dictionaries to validate
        schema: Schema to validate against
        collect_errors: If True, collect all errors before raising.
                       If False (default), raise on first error.
        source: Optional source identifier for error messages

    Returns:
        List of dataclass instances

    Raises:
        ValidationError: If validation fails
    """
    # Create Pydantic model for validation
    pydantic_model = _create_pydantic_model(schema)

    # Create dataclass for output
    dataclass_type = generate_dataclass(schema)

    validation_error = ValidationError(source=source, schema_name=schema.name)
    results: list[Any] = []

    for i, record in enumerate(data):
        try:
            # Validate with Pydantic
            validated = pydantic_model.model_validate(record)

            # Convert to dataclass
            instance = create_instance(dataclass_type, validated.model_dump())
            results.append(instance)

        except PydanticValidationError as e:
            for error in e.errors():
                # Cast the error to dict[str, Any] as that's what we expect
                error_dict: dict[str, Any] = dict(error)
                field_error = _convert_pydantic_error(error_dict, row_index=i + 1)
                validation_error.add_error(
                    field=field_error.field,
                    expected=field_error.expected,
                    got=field_error.got,
                    row=field_error.row,
                    column=field_error.column,
                )

            if not collect_errors:
                validation_error.raise_if_errors()

    # Raise collected errors at the end
    validation_error.raise_if_errors()

    return results


def validate_record(
    record: dict[str, Any],
    schema: Schema,
) -> Any:
    """Validate a single record against a schema.

    Args:
        record: Dictionary to validate
        schema: Schema to validate against

    Returns:
        Dataclass instance

    Raises:
        ValidationError: If validation fails
    """
    results = validate([record], schema)
    return results[0]
