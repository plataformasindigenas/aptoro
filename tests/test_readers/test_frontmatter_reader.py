"""Tests for the front-matter reader."""

import pytest

from aptoro.errors import SourceError
from aptoro.readers import read
from aptoro.readers.base import detect_format
from aptoro.readers.frontmatter_reader import FrontmatterReader


class TestFrontmatterReader:
    def test_read_basic(self):
        content = "---\ntitle: Hello\ntags:\n  - a\n  - b\n---\nBody text here."
        reader = FrontmatterReader()
        result = reader.read(content)
        assert len(result) == 1
        assert result[0]["title"] == "Hello"
        assert result[0]["tags"] == ["a", "b"]
        assert result[0]["body_md"] == "Body text here."

    def test_read_no_body(self):
        content = "---\ntitle: Hello\n---\n"
        reader = FrontmatterReader()
        result = reader.read(content)
        assert len(result) == 1
        assert result[0]["title"] == "Hello"
        assert result[0]["body_md"] == ""

    def test_read_no_frontmatter(self):
        content = "Just some plain markdown text."
        reader = FrontmatterReader()
        with pytest.raises(SourceError, match="does not start with front-matter delimiter"):
            reader.read(content)

    def test_read_invalid_yaml(self):
        content = "---\n: invalid: yaml: [unclosed\n---\nBody."
        reader = FrontmatterReader()
        with pytest.raises(SourceError, match="Invalid YAML"):
            reader.read(content)

    def test_read_custom_body_key(self):
        content = "---\ntitle: Hello\n---\nBody text."
        reader = FrontmatterReader(body_key="content")
        result = reader.read(content)
        assert len(result) == 1
        assert "content" in result[0]
        assert result[0]["content"] == "Body text."
        assert "body_md" not in result[0]

    def test_read_glob_pattern(self, tmp_path):
        for i in range(3):
            (tmp_path / f"post{i}.md").write_text(
                f"---\ntitle: Post {i}\n---\nBody {i}."
            )
        result = read(str(tmp_path / "*.md"))
        assert len(result) == 3
        titles = sorted(r["title"] for r in result)
        assert titles == ["Post 0", "Post 1", "Post 2"]

    def test_read_single_md_file(self, tmp_path):
        md_file = tmp_path / "post.md"
        md_file.write_text("---\ntitle: Single\n---\nSingle body.")
        result = read(str(md_file))
        assert len(result) == 1
        assert result[0]["title"] == "Single"
        assert result[0]["body_md"] == "Single body."

    def test_read_glob_no_match(self, tmp_path):
        with pytest.raises(SourceError, match="No files matched pattern"):
            read(str(tmp_path / "nonexistent" / "*.md"))

    def test_body_whitespace_stripped(self):
        content = "---\ntitle: Hello\n---\n\n  Body text.  \n\n"
        reader = FrontmatterReader()
        result = reader.read(content)
        assert result[0]["body_md"] == "Body text."

    def test_frontmatter_not_dict(self):
        content = "---\n- item1\n- item2\n---\nBody."
        reader = FrontmatterReader()
        with pytest.raises(SourceError, match="must be a YAML mapping"):
            reader.read(content)

    def test_detect_format_md(self):
        assert detect_format("post.md") == "frontmatter"
        assert detect_format("path/to/file.md") == "frontmatter"
        assert detect_format("https://example.com/page.md") == "frontmatter"
