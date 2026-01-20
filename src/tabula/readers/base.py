"""Base reader protocol and utilities."""

from typing import Any, Protocol
from urllib.request import urlopen
from urllib.error import URLError
from pathlib import Path

from tabula.errors import SourceError


class Reader(Protocol):
    """Protocol for data readers.

    All readers must implement a read method that takes string content
    and returns a list of dictionaries.
    """

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse content into a list of records.

        Args:
            content: Raw string content to parse

        Returns:
            List of dictionaries, one per record
        """
        ...


def fetch_content(source: str) -> str:
    """Fetch content from a URL or local file path.

    Args:
        source: URL (http/https) or local file path

    Returns:
        Content as string

    Raises:
        SourceError: If content cannot be fetched
    """
    if source.startswith(("http://", "https://")):
        return _fetch_url(source)
    else:
        return _read_file(source)


def _fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    try:
        with urlopen(url, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except URLError as e:
        raise SourceError(f"Cannot fetch URL {url}: {e}")
    except TimeoutError:
        raise SourceError(f"Timeout fetching URL: {url}")
    except UnicodeDecodeError as e:
        raise SourceError(f"Cannot decode content from {url}: {e}")


def _read_file(path: str) -> str:
    """Read content from a local file."""
    file_path = Path(path)
    if not file_path.exists():
        raise SourceError(f"File not found: {path}")
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise SourceError(f"Cannot read file {path}: {e}")
    except UnicodeDecodeError as e:
        raise SourceError(f"Cannot decode file {path}: {e}")


def detect_format(source: str) -> str:
    """Detect format from source path/URL extension.

    Args:
        source: URL or file path

    Returns:
        Format string: 'csv', 'json', 'yaml', or 'toml'

    Raises:
        SourceError: If format cannot be detected
    """
    # Remove query parameters for URLs
    clean_source = source.split("?")[0]
    lower = clean_source.lower()

    if lower.endswith(".csv"):
        return "csv"
    if lower.endswith(".json"):
        return "json"
    if lower.endswith((".yaml", ".yml")):
        return "yaml"
    if lower.endswith(".toml"):
        return "toml"

    raise SourceError(
        f"Cannot detect format from source: {source}. "
        "Please specify format explicitly."
    )
