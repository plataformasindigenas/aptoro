"""Tests for the aptoro CLI."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from aptoro.cli import main


def test_validate_success(
    capsys: pytest.CaptureFixture[str], sample_csv_path: Path, sample_schema_path: Path
) -> None:
    """Test successful validation via CLI."""
    args = [
        "validate",
        str(sample_csv_path),
        "--schema",
        str(sample_schema_path),
    ]

    # main() doesn't return anything, it prints to stdout
    main(args)

    captured = capsys.readouterr()
    assert "Validation successful." in captured.out
    assert captured.err == ""


def test_validate_failure_file_not_found(
    capsys: pytest.CaptureFixture[str], sample_schema_path: Path
) -> None:
    """Test validation with non-existent data file."""
    args = [
        "validate",
        "non_existent.csv",
        "--schema",
        str(sample_schema_path),
    ]

    with pytest.raises(SystemExit) as excinfo:
        main(args)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error: " in captured.err


def test_validate_failure_schema_not_found(
    capsys: pytest.CaptureFixture[str], sample_csv_path: Path
) -> None:
    """Test validation with non-existent schema file."""
    args = [
        "validate",
        str(sample_csv_path),
        "--schema",
        "non_existent_schema.yaml",
    ]

    with pytest.raises(SystemExit) as excinfo:
        main(args)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error: " in captured.err


def test_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no args shows help."""
    # We need to catch SystemExit because argparse prints help and exits
    with pytest.raises(SystemExit) as excinfo:
        main([])

    # argparse usually exits with 0 when asking for help,
    # but here we trigger help manually inside main if no command provided.
    # However, parse_args(['--help']) inside main will raise SystemExit(0)
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "usage: " in captured.out


def test_explicit_format(
    capsys: pytest.CaptureFixture[str], sample_csv_path: Path, sample_schema_path: Path
) -> None:
    """Test successful validation with explicit format."""
    args = [
        "validate",
        str(sample_csv_path),
        "--schema",
        str(sample_schema_path),
        "--format",
        "csv",
    ]

    main(args)

    captured = capsys.readouterr()
    assert "Validation successful." in captured.out
