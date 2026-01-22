"""Tests for custom types (url, file, datetime)."""

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aptoro.errors import ValidationError
from aptoro.schema.types import BaseType, Field, FieldType, Schema
from aptoro.validation import validate


def create_schema(field_name: str, base_type: BaseType, optional: bool = False) -> Schema:
    return Schema(
        name="test_schema",
        fields=(
            Field(name="id", field_type=FieldType(base=BaseType.STR)),
            Field(name=field_name, field_type=FieldType(base=base_type, optional=optional)),
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

    def test_optional_url(self) -> None:
        schema = create_schema("website", BaseType.URL, optional=True)
        data = [{"id": "1", "website": None}]
        records = validate(data, schema)
        assert records[0].website is None


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

    def test_optional_file(self) -> None:
        schema = create_schema("path", BaseType.FILE, optional=True)
        data = [{"id": "1", "path": None}]
        records = validate(data, schema)
        assert records[0].path is None


class TestDatetimeType:
    def test_validate_iso_datetime(self) -> None:
        schema = create_schema("created_at", BaseType.DATETIME)
        # UTC time
        data = [{"id": "1", "created_at": "2023-01-01T12:00:00Z"}]
        records = validate(data, schema)
        assert records[0].created_at == "2023-01-01T12:00:00+00:00"

        # Offset time
        data = [{"id": "2", "created_at": "2023-01-01T12:00:00+01:00"}]
        records = validate(data, schema)
        # Should be converted to UTC
        # 12:00+01:00 is 11:00 UTC
        assert records[0].created_at == "2023-01-01T11:00:00+00:00"

    def test_validate_date_only(self) -> None:
        schema = create_schema("created_at", BaseType.DATETIME)
        data = [{"id": "1", "created_at": "2023-01-01"}]
        records = validate(data, schema)
        # Should become midnight UTC
        assert records[0].created_at == "2023-01-01T00:00:00+00:00"

    def test_validate_naive_datetime(self) -> None:
        schema = create_schema("created_at", BaseType.DATETIME)
        data = [{"id": "1", "created_at": "2023-01-01T12:00:00"}]
        records = validate(data, schema)
        # Should be assumed UTC
        assert records[0].created_at == "2023-01-01T12:00:00+00:00"

    def test_validate_invalid_format(self) -> None:
        schema = create_schema("created_at", BaseType.DATETIME)
        data = [{"id": "1", "created_at": "not-a-date"}]

        with pytest.raises(ValidationError) as exc:
            validate(data, schema)
        assert "Invalid datetime format" in str(exc.value)

        data = [{"id": "1", "created_at": "01/01/2023"}]  # wrong format
        with pytest.raises(ValidationError) as exc:
            validate(data, schema)
        assert "Invalid datetime format" in str(exc.value)

    def test_optional_datetime(self) -> None:
        schema = create_schema("created_at", BaseType.DATETIME, optional=True)
        data = [{"id": "1", "created_at": None}]
        records = validate(data, schema)
        assert records[0].created_at is None

    def test_default_datetime_normalization(self) -> None:
        schema = Schema(
            name="test",
            fields=(
                Field(name="id", field_type=FieldType(base=BaseType.STR)),
                Field(
                    name="when",
                    field_type=FieldType(
                        base=BaseType.DATETIME, default="2023-01-01", has_default=True
                    ),
                ),
            ),
        )
        data = [{"id": "1"}]  # missing 'when', should use default
        records = validate(data, schema)
        # Should be normalized to UTC ISO string
        assert records[0].when == "2023-01-01T00:00:00+00:00"


class TestEnumType:
    def test_optional_enum(self) -> None:
        schema = Schema(
            name="test",
            fields=(
                Field(name="id", field_type=FieldType(base=BaseType.STR)),
                Field(
                    name="color",
                    field_type=FieldType(
                        base=BaseType.STR, constraints=("red", "blue"), optional=True
                    ),
                ),
            ),
        )
        data = [{"id": "1", "color": None}]
        records = validate(data, schema)
        assert records[0].color is None
