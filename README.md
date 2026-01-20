# Tabula

A minimal, functional Python ETL library for reading, validating, and transforming data using YAML schemas.

## Installation

```bash
pip install tabula
```

## Quick Start

```python
from tabula import load, load_schema, read, validate, to_json

# All-in-one: read + validate
entries = load(source="data.csv", schema="schema.yaml")

# Or step by step:
schema = load_schema("schema.yaml")
data = read("data.csv")
entries = validate(data, schema)

# Export
json_str = to_json(entries)
```

## Schema Language

Define your data schema in YAML:

```yaml
name: lexicon_entry
description: Dictionary entries

fields:
  id: str
  lemma: str
  pos: str[noun|verb|adj|adv]    # Constrained values
  definition: str
  translation: str?               # Optional field
  examples: list[str]?            # Optional list
  frequency: int = 0              # Default value
```

### Type Syntax

- Basic types: `str`, `int`, `float`, `bool`
- Optional: `str?`
- Default value: `str = "default"`, `int = 0`
- Constrained: `str[a|b|c]`
- Lists: `list[str]`, `list[int]`

### Schema Inheritance

```yaml
# child.yaml
name: child_entry
extends: base.yaml

fields:
  name: str
  # inherits fields from base.yaml
```

## Supported Formats

- CSV
- JSON
- YAML
- TOML

## License

MIT
