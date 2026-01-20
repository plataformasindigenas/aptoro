"""CSV reader implementation using stdlib csv module."""

import csv
from io import StringIO
from typing import Any

from tabula.errors import SourceError


class CSVReader:
    """Read CSV content into list of dictionaries.

    Uses csv.DictReader for parsing, with automatic type inference
    for common types (int, float, bool).
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        quotechar: str = '"',
        infer_types: bool = True,
    ):
        """Initialize CSV reader.

        Args:
            delimiter: Field delimiter character
            quotechar: Quote character for fields
            infer_types: Whether to infer int/float/bool from strings
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.infer_types = infer_types

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse CSV content into records.

        Args:
            content: CSV string content

        Returns:
            List of dictionaries with field names as keys
        """
        try:
            reader = csv.DictReader(
                StringIO(content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            records = []
            for row in reader:
                if self.infer_types:
                    row = {k: _infer_type(v) for k, v in row.items()}
                records.append(row)
            return records
        except csv.Error as e:
            raise SourceError(f"CSV parsing error: {e}")


def _infer_type(value: str | None) -> Any:
    """Infer Python type from string value.

    Args:
        value: String value to convert

    Returns:
        Converted value (int, float, bool, None, or original string)
    """
    if value is None or value == "":
        return None

    # Try int
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Try bool
    lower = value.lower()
    if lower in ("true", "yes", "1"):
        return True
    if lower in ("false", "no", "0"):
        return False

    # Keep as string
    return value
