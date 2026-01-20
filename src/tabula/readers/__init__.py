"""Data readers for various formats."""

from typing import Any

from tabula.errors import SourceError
from tabula.readers.base import Reader, detect_format, fetch_content
from tabula.readers.csv_reader import CSVReader
from tabula.readers.json_reader import JSONReader
from tabula.readers.toml_reader import TOMLReader
from tabula.readers.yaml_reader import YAMLReader

__all__ = [
    "CSVReader",
    "JSONReader",
    "Reader",
    "TOMLReader",
    "YAMLReader",
    "detect_format",
    "fetch_content",
    "get_reader",
    "read",
]

# Reader registry
_READERS: dict[str, type[Reader]] = {
    "csv": CSVReader,
    "json": JSONReader,
    "yaml": YAMLReader,
    "yml": YAMLReader,
    "toml": TOMLReader,
}


def get_reader(format: str, **kwargs: Any) -> Reader:
    """Get a reader instance for the specified format.

    Args:
        format: Format name ('csv', 'json', 'yaml', 'toml')
        **kwargs: Additional arguments passed to reader constructor

    Returns:
        Reader instance

    Raises:
        SourceError: If format is not supported
    """
    format = format.lower()
    if format not in _READERS:
        supported = ", ".join(sorted(_READERS.keys()))
        raise SourceError(f"Unsupported format: {format}. Supported: {supported}")

    return _READERS[format](**kwargs)


def read(
    source: str,
    *,
    format: str | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Read data from a source (URL or file path).

    This is the main entry point for reading data. It:
    1. Fetches content from URL or local file
    2. Detects format if not specified
    3. Parses content using appropriate reader

    Args:
        source: URL (http/https) or local file path
        format: Explicit format ('csv', 'json', 'yaml', 'toml').
                If None, detected from source extension.
        **kwargs: Additional arguments passed to reader

    Returns:
        List of dictionaries, one per record

    Raises:
        SourceError: If source cannot be read or parsed

    Examples:
        >>> data = read("https://example.com/data.csv")
        >>> data = read("./local/data.json")
        >>> data = read("https://api.example.com/export", format="json")
    """
    # Detect format if not specified
    if format is None:
        format = detect_format(source)

    # Fetch content
    content = fetch_content(source)

    # Parse with appropriate reader
    reader = get_reader(format, **kwargs)
    return reader.read(content)
