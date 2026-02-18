"""Data readers for various formats."""

import glob as _glob
from typing import Any

from aptoro.errors import SourceError
from aptoro.readers.base import Reader, detect_format, fetch_content
from aptoro.readers.csv_reader import CSVReader
from aptoro.readers.frontmatter_reader import FrontmatterReader
from aptoro.readers.json_reader import JSONReader
from aptoro.readers.toml_reader import TOMLReader
from aptoro.readers.yaml_reader import YAMLReader

__all__ = [
    "CSVReader",
    "FrontmatterReader",
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
    "frontmatter": FrontmatterReader,
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


def _is_glob(source: str) -> bool:
    """Check if source is a glob pattern (not a URL)."""
    if source.startswith(("http://", "https://")):
        return False
    return any(c in source for c in ("*", "?", "["))


def read(
    source: str,
    *,
    format: str | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Read data from a source (URL, file path, or glob pattern).

    This is the main entry point for reading data. It:
    1. Fetches content from URL, local file, or glob-matched files
    2. Detects format if not specified
    3. Parses content using appropriate reader

    Args:
        source: URL (http/https), local file path, or glob pattern
        format: Explicit format ('csv', 'json', 'yaml', 'toml', 'frontmatter').
                If None, detected from source extension.
        **kwargs: Additional arguments passed to reader

    Returns:
        List of dictionaries, one per record

    Raises:
        SourceError: If source cannot be read or parsed

    Examples:
        >>> data = read("https://example.com/data.csv")
        >>> data = read("./local/data.json")
        >>> data = read("encyclopedia/*.md", format="frontmatter")
    """
    if _is_glob(source):
        if format is None:
            format = detect_format(source)
        paths = sorted(_glob.glob(source, recursive=True))
        if not paths:
            raise SourceError(f"No files matched pattern: {source}")
        reader = get_reader(format, **kwargs)
        results: list[dict[str, Any]] = []
        for path in paths:
            content = fetch_content(path)
            results.extend(reader.read(content))
        return results

    # Single file / URL path
    if format is None:
        format = detect_format(source)

    content = fetch_content(source)
    reader = get_reader(format, **kwargs)
    return reader.read(content)
