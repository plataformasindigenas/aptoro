"""Tabula - A minimal, functional Python ETL library.

Tabula reads data from various sources (CSV, JSON, YAML, TOML),
validates it against YAML schemas, and returns typed dataclasses.

Example:
    >>> from tabula import load, load_schema, read, validate, to_json
    >>>
    >>> # All-in-one: read + validate
    >>> entries = load(source="data.csv", schema="schema.yaml")
    >>>
    >>> # Or step by step:
    >>> schema = load_schema("schema.yaml")
    >>> data = read("data.csv")
    >>> entries = validate(data, schema)
    >>>
    >>> # Export
    >>> json_str = to_json(entries)
"""

from typing import Any

from tabula.errors import SchemaError, SourceError, TabulaError, ValidationError
from tabula.output import to_dicts, to_json
from tabula.readers import read
from tabula.schema import Schema, load_schema
from tabula.validation import validate

__version__ = "0.1.0"

__all__ = [
    # Main functions
    "load",
    "load_schema",
    "read",
    "validate",
    # Output
    "to_dicts",
    "to_json",
    # Types
    "Schema",
    # Errors
    "SchemaError",
    "SourceError",
    "TabulaError",
    "ValidationError",
    # Version
    "__version__",
]


def load(
    source: str,
    schema: str | Schema,
    *,
    format: str | None = None,
    collect_errors: bool = False,
    **reader_kwargs: Any,
) -> list[Any]:
    """Load and validate data from a source in one step.

    This is the main convenience function that combines reading and validation.

    Args:
        source: URL (http/https) or local file path to data
        schema: Path to YAML schema file, or Schema object
        format: Explicit format ('csv', 'json', 'yaml', 'toml').
                If None, detected from source extension.
        collect_errors: If True, collect all validation errors before raising.
                       If False (default), raise on first error.
        **reader_kwargs: Additional arguments passed to the reader

    Returns:
        List of validated dataclass instances

    Raises:
        SourceError: If source cannot be read or parsed
        SchemaError: If schema is invalid
        ValidationError: If data doesn't match schema

    Example:
        >>> entries = load("https://example.com/data.csv", "schema.yaml")
        >>> for entry in entries:
        ...     print(entry.lemma, entry.definition)
    """
    # Load schema if path provided
    if isinstance(schema, str):
        schema = load_schema(schema)

    # Read data
    data = read(source, format=format, **reader_kwargs)

    # Validate and return
    return validate(data, schema, collect_errors=collect_errors, source=source)
