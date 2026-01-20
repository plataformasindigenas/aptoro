"""Exception hierarchy for tabula.

All exceptions inherit from TabulaError for easy catching.
"""

from dataclasses import dataclass, field


class TabulaError(Exception):
    """Base exception for all tabula errors."""

    pass


class SchemaError(TabulaError):
    """Raised when a schema definition is invalid."""

    pass


class SourceError(TabulaError):
    """Raised when a data source cannot be read or parsed."""

    pass


@dataclass
class FieldError:
    """Details about a single field validation error."""

    field: str
    expected: str
    got: str
    row: int | None = None
    column: str | None = None

    def __str__(self) -> str:
        location = ""
        if self.row is not None:
            location = f"\n  Location: row {self.row}"
            if self.column:
                location += f', column "{self.column}"'
        return f"  Field: {self.field}\n  Expected: {self.expected}\n  Got: {self.got!r}{location}"


@dataclass
class ValidationError(TabulaError):
    """Raised when data does not match the schema.

    Contains detailed information about all validation failures.
    """

    errors: list[FieldError] = field(default_factory=list)
    source: str | None = None
    schema_name: str | None = None

    def __str__(self) -> str:
        error_count = len(self.errors)
        lines = [f"Validation failed with {error_count} error(s)"]

        if self.source:
            lines.append(f"Source: {self.source}")
        if self.schema_name:
            lines.append(f"Schema: {self.schema_name}")

        lines.append("")

        for i, error in enumerate(self.errors, 1):
            lines.append(f"Error {i}/{error_count}:")
            lines.append(str(error))
            lines.append("")

        return "\n".join(lines)

    def add_error(
        self,
        field: str,
        expected: str,
        got: str,
        row: int | None = None,
        column: str | None = None,
    ) -> None:
        """Add a field error to the collection."""
        self.errors.append(FieldError(field=field, expected=expected, got=got, row=row, column=column))

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def raise_if_errors(self) -> None:
        """Raise self if there are any errors."""
        if self.has_errors():
            raise self
