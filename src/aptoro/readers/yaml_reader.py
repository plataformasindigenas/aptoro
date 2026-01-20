"""YAML reader implementation using PyYAML."""

from typing import Any

import yaml

from aptoro.errors import SourceError


class YAMLReader:
    """Read YAML content into list of dictionaries.

    Expects either:
    - A YAML sequence of mappings
    - A YAML mapping with a 'data' or 'records' key containing a sequence
    """

    def __init__(self, *, data_key: str | None = None):
        """Initialize YAML reader.

        Args:
            data_key: Optional key to extract sequence from root mapping.
                      If None, auto-detects 'data' or 'records' keys,
                      or expects root to be a sequence.
        """
        self.data_key = data_key

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse YAML content into records.

        Args:
            content: YAML string content

        Returns:
            List of dictionaries
        """
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise SourceError(f"YAML parsing error: {e}")

        if data is None:
            return []

        return self._extract_records(data)

    def _extract_records(self, data: Any) -> list[dict[str, Any]]:
        """Extract list of records from parsed YAML."""
        # Direct sequence
        if isinstance(data, list):
            return self._validate_records(data)

        # Mapping with data key
        if isinstance(data, dict):
            if self.data_key:
                if self.data_key not in data:
                    raise SourceError(f"Key '{self.data_key}' not found in YAML")
                return self._validate_records(data[self.data_key])

            # Auto-detect common keys
            for key in ("data", "records", "items", "results"):
                if key in data and isinstance(data[key], list):
                    return self._validate_records(data[key])

            raise SourceError(
                "YAML mapping must contain 'data', 'records', 'items', or 'results' key "
                "with a sequence value, or specify data_key explicitly"
            )

        raise SourceError(f"Expected YAML sequence or mapping, got {type(data).__name__}")

    def _validate_records(self, records: list[Any]) -> list[dict[str, Any]]:
        """Validate that all records are mappings."""
        result = []
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                raise SourceError(f"Record at index {i} is not a mapping: {type(record).__name__}")
            result.append(record)
        return result
