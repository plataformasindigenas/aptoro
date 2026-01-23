# Aptoro

[![PyPI version](https://img.shields.io/pypi/v/aptoro.svg)](https://pypi.org/project/aptoro/)
[![Python versions](https://img.shields.io/pypi/pyversions/aptoro.svg)](https://pypi.org/project/aptoro/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Aptoro** is a Xavante word for *"preparing the arrows for hunting"*.

It is a minimal, functional Python ETL library for reading, validating, and transforming data using YAML schemas. Designed for simplicity and correctness, it bridges the gap between raw data files (CSV, JSON) and typed, validated Python objects.

## Features

- **Schema-First:** Define your data model in simple, readable YAML.
- **Strict Validation:** Ensures data quality with type checks, constraints, and range validation.
- **Rich Types:** Built-in support for `datetime` (ISO 8601), `url`, `file`, and standard primitives.
- **Functional API:** Pure functions and immutable dataclasses make pipelines predictable.
- **Zero Boilerplate:** No complex class definitions—just load your schema and go.

## Installation

```bash
pip install aptoro
```

## CLI Usage

Aptoro provides a command-line interface for validating data files directly.

```bash
# Validate a CSV file against a schema
aptoro validate data.csv --schema schema.yaml

# Explicitly specify format
aptoro validate data.txt --schema schema.yaml --format json
```

## Quick Start

```python
from aptoro import load, load_schema, read, validate, to_json

# All-in-one: read + validate
entries = load(source="data.csv", schema="schema.yaml")

# Or step by step pipeline:
schema = load_schema("schema.yaml")
data = read("data.csv")
entries = validate(data, schema)

# Export to JSON
json_str = to_json(entries)

# Export with embedded metadata (self-describing files)
json_meta = to_json(entries, schema=schema, include_meta=True)
```

## Documentation

For full details on the schema language, advanced validation, and API reference, see the [Documentation](DOCS.md).

## Schema Language

Define your data schema in YAML:

```yaml
name: lexicon_entry
description: Dictionary entries

fields:
  id: str
  lemma: str
  pos: str[noun|verb|adj|adv]     # Constrained values (Enum)
  definition: str
  translation: str?               # Optional field
  examples: list[str]?            # Optional list
  frequency: int = 0              # Default value
  created_at: datetime?           # Optional ISO 8601 datetime
  source_url: url?                # Optional URL
```

### Type Syntax

- **Basic types:** `str`, `int`, `float`, `bool`
- **Specialized types:** `url`, `file`, `datetime`
- **Optional:** `str?`, `int?`, `url?`, `datetime?`
- **Default value:** `str = "default"`, `int = 0`, `datetime = "2024-01-01"`
- **Constrained:** `str[a|b|c]`
- **Lists:** `list[str]`, `list[int]`

See [DOCS.md](DOCS.md) for full syntax, including inheritance and nested structures.

## Supported Formats

- **CSV** (auto-detects types)
- **JSON**
- **YAML**
- **TOML**

## License

GNU General Public License v3 (GPLv3)
