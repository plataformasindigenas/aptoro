"""Tests for custom types (url, file)."""

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aptoro.errors import ValidationError
from aptoro.schema.types import BaseType, Field, FieldType, Schema
from aptoro.validation import validate


def create_schema(field_name: str, base_type: BaseType) -> Schema:
    return Schema(
        name="test_schema",
        fields=(
            Field(name="id", field_type=FieldType(base=BaseType.STR)),
            Field(name=field_name, field_type=FieldType(base=base_type)),
        ),
    )


class TestUrlType:
    def test_validate_valid_url(self) -> None:
        schema = create_schema("website", BaseType.URL)
        data = [{"id": "1", "website": "https://example.com"}]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response

            records = validate(data, schema)
            assert records[0].website == "https://example.com"

    def test_validate_invalid_url_404(self) -> None:
        schema = create_schema("website", BaseType.URL)
        data = [{"id": "1", "website": "https://example.com/404"}]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with pytest.raises(ValidationError) as exc:
                validate(data, schema)
            assert "URL returned status 404" in str(exc.value)

    def test_validate_invalid_url_connection_error(self) -> None:
        schema = create_schema("website", BaseType.URL)
        data = [{"id": "1", "website": "https://invalid-domain.xyz"}]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(ValidationError) as exc:
                validate(data, schema)
            assert "URL validation failed" in str(exc.value)


class TestFileType:
    def test_validate_valid_file(self, tmp_path: Path) -> None:
        # Create a real file for testing
        test_file = tmp_path / "test.txt"
        test_file.touch()

        schema = create_schema("path", BaseType.FILE)
        data = [{"id": "1", "path": str(test_file)}]

        records = validate(data, schema)
        assert records[0].path == str(test_file)

    def test_validate_missing_file(self) -> None:
        schema = create_schema("path", BaseType.FILE)
        data = [{"id": "1", "path": "/non/existent/file.txt"}]

        with pytest.raises(ValidationError) as exc:
            validate(data, schema)
        assert "File not found" in str(exc.value)
