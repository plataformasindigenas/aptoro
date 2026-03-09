# Aptoro Documentation

**Version 0.5.0**

Aptoro is a minimal, functional Python ETL library for reading, validating, and transforming data using YAML schemas. It was designed for linguistic data projects but works with any tabular data.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Installation](#installation)
3. [CLI Usage](#cli-usage)
4. [Quick Start](#quick-start)
5. [Schema Language](#schema-language)
   - [Basic Types](#basic-types)
   - [Optional Fields](#optional-fields)
   - [Default Values](#default-values)
   - [Constrained Values](#constrained-values-enums)
   - [Numeric Range Constraints](#numeric-range-constraints)
   - [Lists](#lists)
   - [Dicts](#dicts)
   - [Nested Objects](#nested-objects)
   - [Schema Metadata](#schema-metadata)
   - [Schema Inheritance](#schema-inheritance)
6. [Reading Data](#reading-data)
   - [Supported Formats](#supported-formats)
   - [Reading from URLs](#reading-from-urls)
   - [Reading from Files](#reading-from-files)
   - [Glob Patterns](#glob-patterns)
   - [Front-Matter (Markdown + YAML)](#front-matter-markdown--yaml)
   - [Reader Options](#reader-options)
7. [Validation](#validation)
   - [Basic Validation](#basic-validation)
   - [Error Collection](#error-collection)
   - [Error Summary and Truncation](#error-summary-and-truncation)
   - [Error Messages](#error-messages)
   - [Null Handling with Defaults](#null-handling-with-defaults)
8. [Output](#output)
   - [To JSON](#to-json)
   - [To Dictionaries](#to-dictionaries)
   - [Embedded Metadata](#embedded-metadata)
9. [API Reference](#api-reference)
10. [Error Types](#error-types)
11. [Examples](#examples)
12. [Design Decisions](#design-decisions)

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

Requirements: Python 3.11+

---

## CLI Usage

Aptoro includes a command-line interface (CLI) for quick validation tasks without writing Python code.

### Validate Command

The `validate` command checks a data file against a schema.

```bash
aptoro validate [source] --schema [schema_path]
```

**Arguments:**

- `source`: Path or URL to the data file.
- `--schema`, `-s`: Path to the YAML schema file (required).
- `--format`, `-f`: Explicit data format (`csv`, `json`, `yaml`, `toml`). If not provided, it is auto-detected from the file extension.

**Examples:**

```bash
# Validate a local CSV file
aptoro validate ./data/records.csv --schema ./schemas/record.yaml

# Validate a remote JSON file
aptoro validate https://example.com/data.json --schema ./schemas/data.yaml

# Validate a file with a non-standard extension
aptoro validate ./data/dump.txt --schema ./schemas/dump.yaml --format json
```

If validation succeeds, it prints "Validation successful.".
If validation fails, it prints a truncated error summary (up to 10 errors) to standard error and exits with code 1. Remaining errors beyond the first 10 are summarized as a count.

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
| `datetime` | `str` | ISO 8601 datetime (normalized to UTC) |

**Smart default**: All fields are **required** unless marked otherwise.

### Optional Fields

Add `?` after the type to make a field optional:

```yaml
fields:
  name: str           # Required
  nickname: str?      # Optional (can be null/missing)
  age: int?           # Optional integer
  website: url?       # Optional URL
  created: datetime?  # Optional datetime
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
  scores: dict[str, int] = {}
  homepage: url = "https://example.com"
  start_date: datetime = "2024-01-01"
```

**Supported default values:**
- Strings: `"text"` or `'text'`
- Integers: `42`
- Floats: `3.14`
- Booleans: `true`, `false`
- Empty list: `[]`
- Empty dict: `{}`
- Null: `null` or `none`

**Note:** Default values are validated against the type. For example, a default for a `datetime` field must be a valid ISO 8601 string, and it will be normalized to UTC in the output.

**Null coalescing:** When a record provides an explicit `null`/`None` for a field that has a default value (and is not optional), Aptoro strips the null and applies the schema default instead. This accommodates sources like YAML/JSON where missing values may appear as explicit nulls. For optional fields without a default, `null` is preserved as `None`.

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

### Datetime Handling

The `datetime` type strictly follows ISO 8601 but is flexible with input:

- **Date only**: `2023-10-27` → `2023-10-27T00:00:00+00:00` (Midnight UTC)
- **Full datetime**: `2023-10-27T14:30:00Z`
- **Offset conversion**: `2023-10-27T14:30:00+02:00` → `2023-10-27T12:30:00+00:00` (Converted to UTC)
- **Naive datetime**: `2023-10-27T14:30:00` → `2023-10-27T14:30:00+00:00` (Assumed UTC)

The output is always a normalized ISO 8601 string with UTC timezone (`+00:00` or `Z`).

### Lists

Use `list[T]` for arrays:

```yaml
fields:
  tags: list[str]           # Required list of strings
  scores: list[int]         # Required list of integers
  items: list[str]?         # Optional list
  defaults: list[str] = []  # List with empty default
```

### Dicts

Use `dict` for key-value mappings. Keys are always strings.

```yaml
fields:
  # Untyped dict (any values)
  metadata: dict?

  # Typed values
  tags: dict[str, str]?        # String values
  scores: dict[str, int] = {}  # Integer values, default empty

  # Shorthand: dict[str] is equivalent to dict[str, str]
  labels: dict[str]?
```

**Syntax variants:**

| Syntax | Meaning |
|--------|---------|
| `dict` | Untyped dict (any values), required |
| `dict?` | Untyped dict, optional |
| `dict[str, int]` | Dict with int values, required |
| `dict[str, str]?` | Dict with string values, optional |
| `dict[str, int] = {}` | Dict with int values, default empty |
| `dict[str]` | Shorthand for `dict[str, str]` |

Dict keys must always be `str`. Specifying a non-`str` key type (e.g., `dict[int, str]`) raises a `SchemaError`.

### Nested Objects

For structured sub-documents, use `type: object` with a `fields` block:

```yaml
name: fauna_entry
fields:
  id: str
  name: str
  infobox:
    type: object
    optional: true
    fields:
      scientific_name: str?
      family: str?
      habitat: str?
  stats:
    type: object
    fields:
      count: int
      label: str = "default"
```

**Object rules:**
- Required by default; add `optional: true` to make nullable
- Nested fields follow the same type syntax as top-level fields (including defaults, optionality, enums, ranges)
- In validated output, objects become plain `dict` values on the frozen dataclass
- Objects can be combined with list nesting (see below)

**Nested lists** use `type: list` with an `items` block for arrays of structured objects:

```yaml
fields:
  senses:
    type: list
    items:
      definition: str
      examples: list[str]?
```

Each item in the list is validated against the `items` sub-schema.

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

---

## Reading Data

### Supported Formats

| Format | Extensions | Auto-detected | Notes |
|--------|------------|---------------|-------|
| CSV | `.csv` | Yes | Auto-infers types (int, float, bool) |
| JSON | `.json` | Yes | Array or object with `data`/`records`/`items`/`results` key |
| YAML | `.yaml`, `.yml` | Yes | Sequence or mapping with `data`/`records`/`items`/`results` key |
| TOML | `.toml` | Yes | Requires `[[records]]` array of tables |
| Front-matter | `.md` | Yes | YAML front matter + markdown body |

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

### Glob Patterns

`read()` supports glob patterns for reading multiple files at once. Each matched file is read and parsed, and all records are concatenated into a single list.

```python
from aptoro import read

# Read all CSV files in a directory
data = read("data/*.csv")

# Read all markdown files recursively
data = read("content/**/*.md")

# Read specific JSON files
data = read("exports/2024-*.json")
```

**Glob rules:**
- A source is treated as a glob if it contains `*`, `?`, or `[` (and is not a URL)
- Files are processed in sorted order (deterministic)
- Format is auto-detected from the pattern's extension (e.g., `*.md` → `frontmatter`)
- Raises `SourceError` if no files match the pattern
- `**` for recursive matching requires `recursive=True` (handled internally)

### Front-Matter (Markdown + YAML)

The front-matter reader parses markdown files with YAML front matter (Jekyll/Hugo/Obsidian style). Each `.md` file becomes one record.

**Input file** (`posts/hello.md`):
```markdown
---
title: Hello World
tags:
  - intro
  - tutorial
date: 2024-01-15
---
This is the body of the post.

It can contain **any markdown**.
```

**Reading:**
```python
from aptoro import read

# Single file (auto-detects frontmatter format from .md extension)
records = read("posts/hello.md")
# [{"title": "Hello World", "tags": ["intro", "tutorial"],
#   "date": "2024-01-15", "body_md": "This is the body of the post.\n\nIt can contain **any markdown**."}]

# Multiple files via glob
records = read("posts/*.md")
# One record per .md file, concatenated
```

**Behavior:**
- Front-matter YAML fields become dict keys
- The markdown body (after the closing `---`) is stored in the `body_md` key, with leading/trailing whitespace stripped
- Content must start with `---\n` and have a closing `---\n` delimiter
- Front matter must parse as a YAML mapping (not a list or scalar)
- Empty front matter produces an empty dict (plus `body_md`)
- Files without front-matter delimiters raise `SourceError`

**Custom body key:**
```python
from aptoro.readers import FrontmatterReader

reader = FrontmatterReader(body_key="content")
records = reader.read(file_content)
# [{"title": "...", "content": "..."}]  # "content" instead of "body_md"
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

### Error Summary and Truncation

When dealing with many errors, use `summary()` to get a truncated view:

```python
try:
    records = validate(data, schema, collect_errors=True)
except ValidationError as e:
    # Show first 10 errors (default), with count of remaining
    print(e.summary())

    # Or customize the limit
    print(e.summary(max_errors=5))
```

`summary()` produces output like:

```
Validation failed with 47 error(s)
Source: data.csv
Schema: lexicon_entry

Error 1/47:
  Field: pos
  Expected: one of [noun, verb, adj, adv]
  Got: "substantivo"
  Location: row 42, column "pos"

...

Error 10/47:
  Field: lemma
  Expected: required field
  Got: null/missing
  Location: row 58, column "lemma"

... and 37 more error(s)
```

The CLI uses `summary()` automatically (with the default limit of 10).

`str(e)` (i.e., `__str__`) still prints all errors without truncation, for programmatic use where you want the full output.

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

### Null Handling with Defaults

When a record contains an explicit `null` for a field that has a schema-defined default:

```yaml
fields:
  frequency: int = 0
  tags: list[str] = []
  definition_pt: str?      # optional, no default
```

```python
data = [{"id": "1", "lemma": "hello", "pos": "noun", "definition": "a greeting",
         "frequency": None, "tags": None, "definition_pt": None}]
records = validate(data, schema)

records[0].frequency     # 0     (default applied)
records[0].tags          # []    (default applied)
records[0].definition_pt # None  (optional field, null preserved)
```

This behavior accommodates YAML/JSON sources where missing values may appear as explicit nulls. The null is stripped before validation, letting Pydantic fill in the schema default. For optional fields (no default), `None` is preserved as-is.

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
    {"id": "1", "name": "Alice", "age": 30}
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
- `source`: URL, file path, or glob pattern
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
data = read("data.csv")          # Single file
data = read("data/*.csv")        # Glob pattern → concatenated records
data = read("posts/*.md")        # Markdown front-matter files
```

**Parameters:**
- `source`: URL, file path, or glob pattern
- `format`: Explicit format (`'csv'`, `'json'`, `'yaml'`, `'toml'`, `'frontmatter'`). Auto-detected from extension if `None`.
- `**kwargs`: Passed to reader constructor

**Returns:** `list[dict[str, Any]]`

**Raises:** `SourceError` if source cannot be read, parsed, or no files match a glob pattern

#### `validate(data, schema, *, collect_errors=False, source=None)`

Validate data against a schema.

```python
records = validate(data, schema)
```

**Parameters:**
- `data`: List of dictionaries to validate
- `schema`: `Schema` object
- `collect_errors`: If `True`, collect all errors before raising. If `False` (default), raise on first error.
- `source`: Optional source identifier for error messages

**Returns:** List of frozen dataclass instances

**Raises:** `ValidationError` if validation fails

#### `validate_record(record, schema)`

Validate a single record (convenience wrapper around `validate()`).

```python
entry = validate_record({"id": "1", "lemma": "hello", "pos": "noun"}, schema)
```

**Returns:** Single dataclass instance

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
schema.fields         # Tuple of Field/NestedField objects
schema.field_names    # Tuple of field names
schema.required_fields  # Tuple of required fields
schema.optional_fields  # Tuple of optional fields

schema.get_field("name")  # Get field by name (or None)
schema.has_field("name")  # Check if field exists
schema.to_dict()          # Serialize to dict (for JSON export / embedded metadata)
```

### Reader Classes

All readers implement the `Reader` protocol: `read(content: str) -> list[dict[str, Any]]`.

| Class | Format | Constructor kwargs |
|-------|--------|--------------------|
| `CSVReader` | CSV | `delimiter`, `quotechar`, `infer_types` |
| `JSONReader` | JSON | `data_key` |
| `YAMLReader` | YAML | `data_key` |
| `TOMLReader` | TOML | *(none)* |
| `FrontmatterReader` | Markdown + YAML | `body_key` (default `"body_md"`) |

Import from `aptoro.readers`:
```python
from aptoro.readers import CSVReader, JSONReader, YAMLReader, TOMLReader, FrontmatterReader
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

**ValidationError attributes and methods:**

```python
try:
    validate(data, schema, collect_errors=True)
except ValidationError as e:
    e.errors       # list[FieldError] — all collected errors
    e.source       # Source identifier (if provided)
    e.schema_name  # Schema name

    str(e)         # Full error output (all errors)
    e.summary()    # Truncated output (default: first 10 errors)
    e.summary(max_errors=5)  # Custom truncation limit
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

### Fauna Encyclopedia (Nested Objects + Front-Matter)

```yaml
# fauna_schema.yaml
name: fauna_entry
fields:
  id: str
  name: str
  infobox:
    type: object
    optional: true
    fields:
      scientific_name: str?
      family: str?
      habitat: str?
  recordings: list[str] = []
  tags: dict[str, str]?
```

```python
from aptoro import load_schema, read, validate

# Read markdown files with front matter
data = read("encyclopedia/*.md")

schema = load_schema("fauna_schema.yaml")
entries = validate(data, schema, collect_errors=True)

for entry in entries:
    print(entry.name)
    if entry.infobox:
        print(f"  Scientific name: {entry.infobox.get('scientific_name')}")
```

### Data Pipeline

```python
from aptoro import load_schema, read, validate, to_json
from aptoro.errors import ValidationError

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
        print(e.summary(max_errors=20))
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

### Cross-Record Validation

Cross-record and cross-schema validation (e.g., foreign key checks) is intentionally out of scope. Aptoro validates each record independently, which keeps the library stateless and simple. Application-specific join semantics are better handled in user code.

---

## File Structure

```
src/aptoro/
├── __init__.py               # Public API: load(), read(), validate(), etc.
├── cli.py                    # CLI: aptoro validate ...
├── errors.py                 # AptoroError, SchemaError, SourceError, ValidationError, FieldError
├── meta.py                   # load_meta() for self-describing JSON files
├── schema/
│   ├── __init__.py
│   ├── types.py              # BaseType, FieldType, Field, NestedField, Schema
│   └── parser.py             # YAML schema parsing, type parsing, inheritance
├── readers/
│   ├── __init__.py           # read(), get_reader(), glob expansion, reader registry
│   ├── base.py               # Reader protocol, fetch_content(), detect_format()
│   ├── csv_reader.py
│   ├── json_reader.py
│   ├── yaml_reader.py
│   ├── toml_reader.py
│   └── frontmatter_reader.py # Markdown + YAML front matter
├── validation/
│   ├── __init__.py
│   ├── validator.py          # Pydantic-based validation, validate(), validate_record()
│   └── dataclass_gen.py      # Dynamic frozen dataclass generation
└── output/
    ├── __init__.py
    └── json_writer.py        # to_json(), to_dicts()
```

---

## License

GPLv3

---

*Documentation for Aptoro v0.5.0 — A project of Plataformas Indigenas*
