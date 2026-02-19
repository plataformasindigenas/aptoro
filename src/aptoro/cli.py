"""Command-line interface for aptoro."""

import argparse
import sys

from aptoro import load
from aptoro.errors import AptoroError, ValidationError


def validate_command(args: argparse.Namespace) -> None:
    """Handle the validate command."""
    try:
        load(
            source=args.source,
            schema=args.schema,
            format=args.format,
            collect_errors=True,
        )
        print("Validation successful.")
    except ValidationError as e:
        print(f"Error: {e.summary()}", file=sys.stderr)
        sys.exit(1)
    except AptoroError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Aptoro - Data validation and transformation utility."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate data against a schema")
    validate_parser.add_argument(
        "source", help="Path or URL to the data file (CSV, JSON, YAML, TOML)"
    )
    validate_parser.add_argument(
        "--schema", "-s", required=True, help="Path to the YAML schema file"
    )
    validate_parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "yaml", "toml"],
        help="Explicit data format (default: auto-detect)",
    )

    return parser.parse_args(args)


def main(args: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parsed_args = parse_args(args)

    if parsed_args.command == "validate":
        validate_command(parsed_args)
    else:
        # If no command is provided, show help
        parse_args(["--help"])


if __name__ == "__main__":
    main()
