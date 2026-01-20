# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/plataformasindigenas/aptoro/releases/tag/v0.1.0
