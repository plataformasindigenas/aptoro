"""Tests for the datetime type."""

import pytest
from datetime import datetime, timezone, date

from aptoro.errors import ValidationError
from aptoro.schema.types import BaseType, Field, FieldType, Schema
from aptoro.validation import validate


def create_schema(field_name: str) -> Schema:
    return Schema(
        name="test_schema",
        fields=(
            Field(name="id", field_type=FieldType(base=BaseType.STR)),
            Field(name=field_name, field_type=FieldType(base=BaseType.DATETIME)),
        ),
    )


class TestDatetimeType:
    def test_validate_iso_datetime(self) -> None:
        schema = create_schema("created_at")
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
        schema = create_schema("created_at")
        data = [{"id": "1", "created_at": "2023-01-01"}]
        records = validate(data, schema)
        # Should become midnight UTC
        assert records[0].created_at == "2023-01-01T00:00:00+00:00"

    def test_validate_naive_datetime(self) -> None:
        schema = create_schema("created_at")
        data = [{"id": "1", "created_at": "2023-01-01T12:00:00"}]
        records = validate(data, schema)
        # Should be assumed UTC
        assert records[0].created_at == "2023-01-01T12:00:00+00:00"

    def test_validate_invalid_format(self) -> None:
        schema = create_schema("created_at")
        data = [{"id": "1", "created_at": "not-a-date"}]

        with pytest.raises(ValidationError) as exc:
            validate(data, schema)
        assert "Invalid datetime format" in str(exc.value)

        data = [{"id": "1", "created_at": "01/01/2023"}]  # wrong format
        with pytest.raises(ValidationError) as exc:
            validate(data, schema)
        assert "Invalid datetime format" in str(exc.value)
