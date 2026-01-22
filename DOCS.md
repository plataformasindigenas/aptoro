# Aptoro Documentation

**Version 0.2.0**

Aptoro is a minimal, functional Python ETL library for reading, validating, and transforming data using YAML schemas. It was designed for linguistic data projects but works with any tabular data.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Schema Language](#schema-language)
   - [Basic Types](#basic-types)
   - [Optional Fields](#optional-fields)
   - [Default Values](#default-values)
   - [Constrained Values](#constrained-values-enums)
   - [Numeric Range Constraints](#numeric-range-constraints)
   - [Lists](#lists)
   - [Schema Metadata](#schema-metadata)
   - [Schema Inheritance](#schema-inheritance)
   - [Nested Structures](#nested-structures)
5. [Reading Data](#reading-data)
   - [Supported Formats](#supported-formats)
   - [Reading from URLs](#reading-from-urls)
   - [Reading from Files](#reading-from-files)
   - [Reader Options](#reader-options)
6. [Validation](#validation)
   - [Basic Validation](#basic-validation)
   - [Error Collection](#error-collection)
   - [Error Messages](#error-messages)
7. [Output](#output)
   - [To JSON](#to-json)
   - [To Dictionaries](#to-dictionaries)
   - [Embedded Metadata](#embedded-metadata)
8. [API Reference](#api-reference)
9. [Error Types](#error-types)
10. [Examples](#examples)
11. [Design Decisions](#design-decisions)

---

## Philosophy

Aptoro follows three core principles:

1. **Smart defaults, expert configurability**: The library assumes sensible defaults (fields are required, no default values) while allowing full control when needed. You write less YAML for common cases.

2. **Functional approach**: Pure functions, immutable dataclasses, composition over inheritance. Data flows through the pipeline: read → validate → transform.

3. **Minimal dependencies**: Only two runtime dependencies (`pyyaml`, `pydantic`). Standard library used wherever possible.

---

## Installation

```bash
pip install aptoro
```

For development:

```bash
pip install aptoro[dev]
```

**Requirements**: Python 3.11+

---

## Quick Start

```python
from aptoro import load

# Define a schema (schema.yaml)
"""
name: person
fields:
  id: str
  name: str
  age: int
  email: str?
"""

# Load and validate data
people = load("data.csv", "schema.yaml")

# Access as typed objects
for person in people:
    print(f"{person.name} is {person.age} years old")
```

**Step-by-step approach:**

```python
from aptoro import load_schema, read, validate, to_json

# 1. Load schema
schema = load_schema("schema.yaml")

# 2. Read raw data
data = read("data.csv")  # Returns list of dicts

# 3. Validate and convert to dataclasses
records = validate(data, schema)

# 4. Export
json_output = to_json(records)
```

---

## Schema Language

Schemas are defined in YAML files. The syntax is designed to be readable by non-programmers while remaining precise.

### Basic Types

```yaml
name: my_schema
fields:
  text_field: str
  number_field: int
  decimal_field: float
  flag_field: bool
```

| Type | Python | Description |
|------|--------|-------------|
| `str` | `str` | Text/string |
| `int` | `int` | Integer |
| `float` | `float` | Decimal number |
| `bool` | `bool` | True/False |
| `url` | `str` | URL (validated for accessibility, 10s timeout) |
| `file` | `str` | File path (validated for existence) |

**Smart default**: All fields are **required** unless marked otherwise.

### Optional Fields

Add `?` after the type to make a field optional:

```yaml
fields:
  name: str           # Required
  nickname: str?      # Optional (can be null/missing)
  age: int?           # Optional integer
```

Optional fields default to `None` when not provided.

### Default Values

Use `= value` to specify a default:

```yaml
fields:
  status: str = "draft"
  count: int = 0
  enabled: bool = true
  tags: list[str] = []
```

**Supported default values:**
- Strings: `"text"` or `'text'`
- Integers: `42`
- Floats: `3.14`
- Booleans: `true`, `false`
- Empty list: `[]`
- Empty dict: `{}`
- Null: `null` or `none`

### Constrained Values (Enums)

Restrict a string field to specific values using `str[value1|value2|...]`:

```yaml
fields:
  status: str[draft|published|archived]
  pos: str[noun|verb|adj|adv]
  priority: str[low|medium|high]
```

Validation will fail if the data contains any value not in the list.

### Numeric Range Constraints

Restrict int/float fields to a range of values using `[min..max]`:

```yaml
fields:
  age: int[0..120]           # Integer between 0 and 120
  score: float[0.0..1.0]     # Float between 0.0 and 1.0
  quantity: int[1..]         # Integer >= 1 (no upper limit)
  temperature: float[..100]  # Float <= 100 (no lower limit)
```

**Range syntax:**
- `int[1..10]` - Value must be >= 1 and <= 10
- `int[..10]` - Value must be <= 10
- `int[5..]` - Value must be >= 5
- `float[-273.15..0]` - Supports negative numbers and decimals

The range is inclusive: values equal to min or max are valid.

### Lists

Use `list[T]` for arrays:

```yaml
fields:
  tags: list[str]           # Required list of strings
  scores: list[int]         # Required list of integers
  items: list[str]?         # Optional list
  defaults: list[str] = []  # List with empty default
```

### Schema Metadata

```yaml
name: lexicon_entry                    # Required: identifier
description: Dictionary entries        # Optional: human description
version: "1.0"                         # Optional: version string
primary_key: entry_id                  # Optional: defaults to "id"

fields:
  entry_id: str
  # ...
```

The `primary_key` field identifies which field serves as the unique identifier. This is informational (used for error messages) and defaults to `"id"`.

### Schema Inheritance

Schemas can extend other schemas using `extends`:

```yaml
# base.yaml
name: base_record
fields:
  id: str
  created_at: str?
  updated_at: str?
```

```yaml
# article.yaml
name: article
extends: base.yaml

fields:
  title: str
  body: str
  author: str?
```

The `article` schema will have all fields from `base.yaml` plus its own fields.

**Inheritance rules:**
- Child fields override parent fields with the same name
- Multiple inheritance: `extends: [base.yaml, timestamps.yaml]`
- Paths are relative to the schema file location

### Nested Structures

For complex data, you can define nested structures:

```yaml
fields:
  id: str
  name: str
  addresses:
    type: list
    items:
      street: str
      city: str
      country: str?
```

**Note**: Nested structures are supported but not favored. Prefer flat structures when possible for simplicity.

---

## Reading Data

### Supported Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| CSV | `.csv` | Auto-infers types (int, float, bool) |
| JSON | `.json` | Array or object with `data`/`records` key |
| YAML | `.yaml`, `.yml` | Sequence or mapping with `data` key |
| TOML | `.toml` | Requires `[[records]]` array of tables |

### Reading from URLs

```python
from aptoro import read

# HTTP/HTTPS URLs
data = read("https://example.com/data.csv")
data = read("https://api.example.com/export.json")
```

### Reading from Files

```python
from aptoro import read

# Local files (absolute or relative paths)
data = read("./data/records.csv")
data = read("/home/user/data.json")
```

### Reader Options

**Explicit format:**

```python
# When URL doesn't have extension
data = read("https://api.example.com/export", format="json")
```

**CSV options:**

```python
from aptoro.readers import CSVReader

reader = CSVReader(
    delimiter=";",        # Field separator (default: ",")
    quotechar="'",        # Quote character (default: '"')
    infer_types=False,    # Disable type inference (keep as strings)
)
data = reader.read(content)
```

**JSON/YAML with custom data key:**

```python
from aptoro.readers import JSONReader

# For {"results": [...]} instead of {"data": [...]}
reader = JSONReader(data_key="results")
data = reader.read(content)
```

---

## Validation

### Basic Validation

```python
from aptoro import load_schema, validate

schema = load_schema("schema.yaml")
data = [
    {"id": "1", "name": "Alice", "age": 30},
    {"id": "2", "name": "Bob", "age": 25},
]

records = validate(data, schema)
# Returns: [Person(id='1', name='Alice', age=30), ...]
```

The returned objects are **frozen dataclasses** — immutable and typed.

### Error Collection

By default, validation stops at the first error. To collect all errors:

```python
try:
    records = validate(data, schema, collect_errors=True)
except ValidationError as e:
    print(f"Found {len(e.errors)} errors:")
    for error in e.errors:
        print(f"  Row {error.row}: {error.field} - {error.expected}")
```

### Error Messages

Aptoro provides clear, actionable error messages:

```
ValidationError: Validation failed with 2 error(s)
Source: https://example.com/data.csv
Schema: lexicon_entry

Error 1/2:
  Field: pos
  Expected: one of [noun, verb, adj, adv]
  Got: "substantivo"
  Location: row 42, column "pos"

Error 2/2:
  Field: lemma
  Expected: required field
  Got: null/missing
  Location: row 58, column "lemma"
```

---

## Output

### To JSON

```python
from aptoro import to_json

json_string = to_json(records)                    # Pretty-printed (indent=2)
json_compact = to_json(records, indent=None)      # Compact
json_ascii = to_json(records, ensure_ascii=True)  # Escape non-ASCII
```

### To Dictionaries

```python
from aptoro import to_dicts

dict_list = to_dicts(records)
# [{'id': '1', 'name': 'Alice', ...}, ...]
```

### Embedded Metadata

You can include the schema metadata in the output file, making it self-describing and portable. This is useful for downstream tools that need to know the schema (types, optionality, etc.).

```python
# Export with metadata
json_with_meta = to_json(records, schema=schema, include_meta=True)
```

The output structure will be:

```json
{
  "meta": {
    "schema_name": "person",
    "version": "1.0",
    "primary_key": "id",
    "generated_at": "2023-10-27T10:00:00Z",
    "fields": {
      "id": "str",
      "name": "str",
      "age": "int"
    }
  },
  "data": [
    {"id": "1", "name": "Alice", "age": 30},
    ...
  ]
}
```

To load this back:

```python
from aptoro import load_meta

# Returns the reconstructed Schema object and the raw data list
schema, data = load_meta("output_with_meta.json")

# You can then validate as usual
records = validate(data, schema)
```

---

## API Reference

### Main Functions

#### `load(source, schema, *, format=None, collect_errors=False, **kwargs)`

All-in-one function: read + validate.

```python
records = load("data.csv", "schema.yaml")
records = load("data.csv", schema_object)  # Can pass Schema directly
```

**Parameters:**
- `source`: URL or file path
- `schema`: Path to schema file or `Schema` object
- `format`: Explicit format (optional, auto-detected)
- `collect_errors`: Collect all errors before raising (default: `False`)
- `**kwargs`: Passed to reader

**Returns:** List of dataclass instances

#### `load_meta(source)`

Load a JSON file with embedded metadata (exported with `include_meta=True`).

```python
schema, data = load_meta("output.json")
```

**Returns:** Tuple of `(Schema, list[dict])`

#### `load_schema(path)`

Load a schema from a YAML file.

```python
schema = load_schema("schema.yaml")
```

**Returns:** `Schema` object

#### `read(source, *, format=None, **kwargs)`

Read data from a source without validation.

```python
data = read("data.csv")  # Returns list of dicts
```

**Returns:** `list[dict[str, Any]]`

#### `validate(data, schema, *, collect_errors=False, source=None)`

Validate data against a schema.

```python
records = validate(data, schema)
```

**Returns:** List of dataclass instances

#### `to_json(records, *, schema=None, include_meta=False, indent=2, ensure_ascii=False)`

Convert records to JSON string.

If `include_meta=True`, `schema` must be provided. Returns a JSON object with `meta` and `data` keys.

#### `to_dicts(records, *, schema=None, include_meta=False)`

Convert records to list of dictionaries (or dict with metadata).

If `include_meta=True`, `schema` must be provided. Returns `{'meta': ..., 'data': [...]}`.

### Schema Object

```python
schema = load_schema("schema.yaml")

schema.name           # Schema name
schema.description    # Optional description
schema.version        # Optional version
schema.primary_key    # Primary key field name (default: "id")
schema.fields         # Tuple of Field objects
schema.field_names    # Tuple of field names
schema.required_fields  # Tuple of required fields
schema.optional_fields  # Tuple of optional fields

schema.get_field("name")  # Get field by name (or None)
schema.has_field("name")  # Check if field exists
```

---

## Error Types

All errors inherit from `AptoroError`:

```python
from aptoro.errors import (
    AptoroError,       # Base exception
    SchemaError,       # Invalid schema definition
    SourceError,       # Cannot read/parse source
    ValidationError,   # Data doesn't match schema
)
```

**ValidationError attributes:**

```python
try:
    validate(data, schema)
except ValidationError as e:
    e.errors       # List of FieldError objects
    e.source       # Source identifier (if provided)
    e.schema_name  # Schema name
```

**FieldError attributes:**

```python
for error in e.errors:
    error.field     # Field name
    error.expected  # What was expected
    error.got       # What was received
    error.row       # Row number (1-indexed)
    error.column    # Column name
```

---

## Examples

### Linguistic Dictionary

```yaml
# bororo_schema.yaml
name: bororo_entry
description: Bororo language dictionary entry

fields:
  id: str
  lemma: str
  pos: str[noun|verb|adj|adv|particle|interjection]
  gloss_pt: str
  gloss_en: str?
  phonetic: str?
  examples: list[str]?
  semantic_domain: str?
  sources: list[str] = []
```

```python
from aptoro import load, to_json

entries = load(
    "https://example.com/bororo-dictionary.csv",
    "bororo_schema.yaml"
)

# Filter verbs
verbs = [e for e in entries if e.pos == "verb"]

# Export subset
print(to_json(verbs))
```

### Data Pipeline

```python
from aptoro import load_schema, read, validate, to_json

def process_linguistic_data(source_url: str, schema_path: str) -> str:
    """Load, validate, and transform linguistic data."""

    # Load schema
    schema = load_schema(schema_path)

    # Read raw data
    raw_data = read(source_url)

    # Validate
    try:
        records = validate(raw_data, schema, collect_errors=True)
    except ValidationError as e:
        # Log errors and continue with valid records
        print(f"Warning: {len(e.errors)} validation errors")
        # Re-validate without error collection to get partial results
        # (In a real app, you'd filter invalid rows)
        raise

    # Transform: add computed fields
    enriched = []
    for record in records:
        d = record.__dict__.copy()
        d['has_examples'] = bool(record.examples)
        d['gloss_length'] = len(record.gloss_pt)
        enriched.append(d)

    return to_json(enriched)
```

### Schema Composition

```yaml
# schemas/base.yaml
name: base_linguistic
fields:
  id: str
  created_at: str?
  source_file: str?
```

```yaml
# schemas/lexicon.yaml
name: lexicon_entry
extends: base.yaml

fields:
  lemma: str
  definition: str
```

```yaml
# schemas/corpus.yaml
name: corpus_sentence
extends: base.yaml

fields:
  text: str
  translation: str?
  tokens: list[str]
```

```python
# Both schemas inherit id, created_at, source_file
lexicon_schema = load_schema("schemas/lexicon.yaml")
corpus_schema = load_schema("schemas/corpus.yaml")
```

---

## Design Decisions

### Why YAML for Schemas?

YAML is more readable for non-programmers (linguists, researchers) than JSON or Python code. The custom type syntax (`str?`, `str[a|b]`) adds expressiveness without complexity.

### Why Pydantic?

Pydantic v2 provides fast validation with excellent error messages. It handles type coercion (e.g., `"42"` → `42` for int fields) gracefully.

### Why Frozen Dataclasses?

Immutability prevents accidental modification and makes the functional pipeline clearer. If you need to modify data, convert to dicts first.

### Why Minimal Dependencies?

The linguistic/academic context often involves environments with limited package management. Two dependencies (`pyyaml`, `pydantic`) is a reasonable minimum.

### Type Coercion

Aptoro coerces types when reasonable:
- Numbers to strings: `42` → `"42"` (for str fields)
- Strings to numbers: `"42"` → `42` (for int fields)
- Various bool representations: `"true"`, `"yes"`, `"1"` → `True`

This accommodates CSV data where everything starts as strings.

---

## License

GPLv3

---

*Documentation for Aptoro v0.2.0 — A project of Plataformas Indígenas*
