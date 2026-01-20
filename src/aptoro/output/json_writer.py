"""JSON output writer."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def to_json(
    records: list[Any],
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> str:
    """Convert records to JSON string.

    Args:
        records: List of dataclass instances
        indent: Indentation level (None for compact output)
        ensure_ascii: If True, escape non-ASCII characters

    Returns:
        JSON string
    """
    data = to_dicts(records)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)


def to_dicts(records: list[Any]) -> list[dict[str, Any]]:
    """Convert records to list of dictionaries.

    Args:
        records: List of dataclass instances

    Returns:
        List of dictionaries
    """
    result = []
    for record in records:
        if is_dataclass(record) and not isinstance(record, type):
            result.append(asdict(record))
        elif isinstance(record, dict):
            result.append(record)
        else:
            raise TypeError(f"Expected dataclass or dict, got {type(record).__name__}")
    return result
