# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-03-09

### Added
- Regex pattern validation for string fields using `str[/regex/]` schema syntax.
- Primary key uniqueness enforcement during validation.

### Changed
- String enum constraints now accept any non-empty pipe-separated values (including spaces, hyphens, and Unicode characters).

## [0.4.0] - 2026-02-19

### Added
- Dict types in schemas: `dict`, `dict?`, `dict[str, int]`, `dict[str, str] = {}`, `dict[str]` shorthand.
- Nested object types: `type: object` with `fields` block for structured sub-documents.
- Front-matter reader for markdown files with YAML front matter (`.md` auto-detected).
- Glob pattern support in `read()`: `read("data/*.md")` reads and concatenates multiple files.
- `ValidationError.summary(max_errors=10)` for truncated error output.
- Null coalescing: explicit `null` on fields with defaults applies the schema default instead of failing.

### Changed
- CLI validation errors now use `summary()` (truncated to 10 errors by default).
- CLI `--format` choices now include `frontmatter`.

## [0.3.1] - 2026-01-23

### Added
- Command-line interface (`aptoro validate ...`) for easier scripting and quick validation.

## [0.3.0] - 2026-01-23

### Added
- New `datetime` datatype with strict ISO 8601 validation and UTC normalization.
- Support for `datetime` fields in schemas (e.g., `created: datetime`).
- Automatic conversion of date-only strings to UTC datetimes.
- Support for optional (`?`) and default values (`= value`) for all types, including `url`, `file`, and `datetime`.

### Changed
- Improved schema parsing to consistently handle optional/default modifiers for all base types.
- Updated documentation with new type features and badges.
- `url` and `file` types now correctly respect optional flags.

## [0.2.0] - 2026-01-21

### Added
- Support for embedded metadata in JSON export (`to_json(include_meta=True)`)
- `load_meta()` function to read JSON files with embedded metadata
- `Schema.to_dict()` method for schema serialization

## [0.1.0] - 2026-01-20

### Added
- Initial release of Aptoro
- Core ETL functionality: read, validate, and transform data
- Support for CSV, JSON, YAML, and TOML file formats
- YAML schema validation with functional approach
- Type-safe dataclass generation from schemas
- JSON output formatting
- Google Sheets integration (optional dependency)
- SQL database support (optional dependency)
- Excel file support (optional dependency)

### Changed
- Renamed project from "tabula" to "aptoro" (Xavante word meaning "preparing the arrows for hunting")
- Changed license from MIT to GPLv3

### Fixed
- All linter errors (ruff)
- All type check errors (mypy)

### Changed
- Package source directory from `src/tabula` to `src/aptoro`
- TabulaError renamed to AptoroError
- Updated all documentation and imports

[0.5.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.5.0
[0.4.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.4.0
[0.3.1]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.3.1
[0.3.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.3.0
[0.2.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.2.0
[0.1.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.1.0
