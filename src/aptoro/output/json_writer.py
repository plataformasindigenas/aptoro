"""JSON output writer."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from aptoro.schema.types import Schema


def to_json(
    records: list[Any],
    *,
    schema: Schema | None = None,
    include_meta: bool = False,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> str:
    """Convert records to JSON string.

    Args:
        records: List of dataclass instances or dicts
        schema: Schema object (required if include_meta=True)
        include_meta: If True, wrap data with schema metadata
        indent: Indentation level (None for compact output)
        ensure_ascii: If True, escape non-ASCII characters

    Returns:
        JSON string. If include_meta=True, returns {"meta": {...}, "data": [...]}

    Raises:
        ValueError: If include_meta=True but schema is not provided
    """
    data = to_dicts(records, schema=schema, include_meta=include_meta)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)


def to_dicts(
    records: list[Any],
    *,
    schema: Schema | None = None,
    include_meta: bool = False,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Convert records to list of dictionaries or dict with metadata.

    Args:
        records: List of dataclass instances or dicts
        schema: Schema object (required if include_meta=True)
        include_meta: If True, wrap data with schema metadata

    Returns:
        list[dict] if include_meta=False
        {"meta": {...}, "data": [...]} if include_meta=True

    Raises:
        ValueError: If include_meta=True but schema is not provided
    """
    if include_meta and schema is None:
        raise ValueError("schema is required when include_meta=True")

    result = []
    for record in records:
        if is_dataclass(record) and not isinstance(record, type):
            result.append(asdict(record))
        elif isinstance(record, dict):
            result.append(record)
        else:
            raise TypeError(f"Expected dataclass or dict, got {type(record).__name__}")

    if not include_meta:
        return result

    meta = schema.to_dict()
    meta["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "meta": meta,
        "data": result,
    }
