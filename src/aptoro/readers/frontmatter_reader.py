"""Front-matter reader for markdown files with YAML front matter."""

from typing import Any

import yaml

from aptoro.errors import SourceError


class FrontmatterReader:
    """Read markdown files with YAML front matter into records.

    Expects content starting with ``---`` delimiters enclosing YAML front
    matter, optionally followed by a markdown body.  Each content string
    produces a single-element list containing one dict.

    Example input::

        ---
        title: Hello
        tags: [a, b]
        ---
        Body text here.

    Result::

        [{"title": "Hello", "tags": ["a", "b"], "body_md": "Body text here."}]
    """

    def __init__(self, *, body_key: str = "body_md") -> None:
        self.body_key = body_key

    def read(self, content: str) -> list[dict[str, Any]]:
        """Parse front-matter content into a single-element record list."""
        if not content.startswith("---\n") and not content.startswith("---\r\n"):
            raise SourceError(
                "Content does not start with front-matter delimiter '---'"
            )

        # Find the closing delimiter
        # Skip the opening "---\n" then look for the next "---"
        rest = content[content.index("\n") + 1 :]
        end_idx = rest.find("\n---")
        if end_idx == -1:
            raise SourceError(
                "Missing closing front-matter delimiter '---'"
            )

        front_matter_str = rest[:end_idx]
        # Skip past "\n---\n" (or "\n---" at EOF)
        after_closing = rest[end_idx + 4 :]  # len("\n---") == 4
        if after_closing.startswith("\n"):
            body = after_closing[1:]
        elif after_closing.startswith("\r\n"):
            body = after_closing[2:]
        else:
            body = after_closing

        try:
            data = yaml.safe_load(front_matter_str)
        except yaml.YAMLError as e:
            raise SourceError(f"Invalid YAML in front matter: {e}")

        if data is None:
            data = {}

        if not isinstance(data, dict):
            raise SourceError(
                f"Front matter must be a YAML mapping, got {type(data).__name__}"
            )

        record = dict(data)
        record[self.body_key] = body.strip()
        return [record]
