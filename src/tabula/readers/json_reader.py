"""JSON reader implementation using stdlib json module."""

import json
from typing import Any

from tabula.errors import SourceError


class JSONReader:
    """Read JSON content into list of dictionaries.

    Expects either:
    - A JSON array of objects: [{"a": 1}, {"a": 2}]
    - A JSON object with a 'data' or 'records' key containing an array
    """

    def __init__(self, *, data_key: str | None = None):
        """Initialize JSON reader.

        Args:
            data_key: Optional key to extract array from root object.
                      If None, auto-detects 'data' or 'records' keys,
                      or expects root to be an array.
        """
        self.data_key = data_key

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse JSON content into records.

        Args:
            content: JSON string content

        Returns:
            List of dictionaries
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise SourceError(f"JSON parsing error: {e}")

        return self._extract_records(data)

    def _extract_records(self, data: Any) -> list[dict[str, Any]]:
        """Extract list of records from parsed JSON."""
        # Direct array
        if isinstance(data, list):
            return self._validate_records(data)

        # Object with data key
        if isinstance(data, dict):
            if self.data_key:
                if self.data_key not in data:
                    raise SourceError(f"Key '{self.data_key}' not found in JSON")
                return self._validate_records(data[self.data_key])

            # Auto-detect common keys
            for key in ("data", "records", "items", "results"):
                if key in data and isinstance(data[key], list):
                    return self._validate_records(data[key])

            raise SourceError(
                "JSON object must contain 'data', 'records', 'items', or 'results' key "
                "with an array value, or specify data_key explicitly"
            )

        raise SourceError(f"Expected JSON array or object, got {type(data).__name__}")

    def _validate_records(self, records: list[Any]) -> list[dict[str, Any]]:
        """Validate that all records are dictionaries."""
        result = []
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                raise SourceError(
                    f"Record at index {i} is not an object: {type(record).__name__}"
                )
            result.append(record)
        return result
