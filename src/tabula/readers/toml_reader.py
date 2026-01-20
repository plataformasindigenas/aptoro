"""TOML reader implementation using stdlib tomllib (Python 3.11+)."""

import tomllib
from typing import Any

from tabula.errors import SourceError


class TOMLReader:
    """Read TOML content into list of dictionaries.

    TOML doesn't support root-level arrays, so expects a mapping with
    a 'data' or 'records' key (or custom key) containing an array of tables.

    Example TOML:
        [[records]]
        id = "1"
        name = "foo"

        [[records]]
        id = "2"
        name = "bar"
    """

    def __init__(self, *, data_key: str | None = None):
        """Initialize TOML reader.

        Args:
            data_key: Key to extract array from root mapping.
                      If None, auto-detects 'data' or 'records' keys.
        """
        self.data_key = data_key

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse TOML content into records.

        Args:
            content: TOML string content

        Returns:
            List of dictionaries
        """
        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            raise SourceError(f"TOML parsing error: {e}")

        return self._extract_records(data)

    def _extract_records(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract list of records from parsed TOML."""
        if self.data_key:
            if self.data_key not in data:
                raise SourceError(f"Key '{self.data_key}' not found in TOML")
            records = data[self.data_key]
        else:
            # Auto-detect common keys
            records = None
            for key in ("data", "records", "items", "results"):
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    break

            if records is None:
                raise SourceError(
                    "TOML must contain 'data', 'records', 'items', or 'results' key "
                    "with an array value, or specify data_key explicitly"
                )

        return self._validate_records(records)

    def _validate_records(self, records: Any) -> list[dict[str, Any]]:
        """Validate that records is a list of tables."""
        if not isinstance(records, list):
            raise SourceError(f"Expected array, got {type(records).__name__}")

        result = []
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                raise SourceError(
                    f"Record at index {i} is not a table: {type(record).__name__}"
                )
            result.append(record)
        return result
