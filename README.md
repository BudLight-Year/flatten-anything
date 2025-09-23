# Flatten Anything 🔨

*Stop writing custom parsers for every data format. Flatten anything.*

[![PyPI](https://img.shields.io/pypi/v/flatten-anything?color=blue)](https://pypi.org/project/flatten-anything/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

Every data pipeline starts the same way: "I have this nested JSON file, and I need to flatten it." Then next week: "Now it's XML." Then: "The client sent Excel files." Before you know it, you have 200 lines of custom parsing code for each format.

## The Solution
```python
from flatten_anything import flatten, ingest

# That's it. That's the whole library.
data = ingest('your_nightmare_file.json')
flat = flatten(data)
```

**It just works.** No matter what format. No matter how nested.

## What's New in v1.1

### 🚀 Streaming Support
Process files larger than memory without breaking a sweat:
```python
# Stream a 10GB CSV file
for chunk in ingest('huge_file.csv', stream=True):
    flat = flatten(chunk)
    # Process each chunk without loading entire file
```

### 🎯 Smarter Flattening
New `records` parameter intelligently handles multiple records:
```python
# Automatically flattens each record separately (new default!)
data = ingest('users.csv')
flat = flatten(data)  # Returns list of flattened records

# Or treat as single structure when needed
flat = flatten(data, records=False)  # Flattens entire structure
```

## Installation

### Basic Installation
```bash
# Core installation (JSON, CSV, YAML, XML, API support)
pip install flatten-anything
```

### With Optional Format Support
```bash
# Add Parquet support
pip install flatten-anything[parquet]

# Add Excel support
pip install flatten-anything[excel]

# Install everything
pip install flatten-anything[all]
```

### Format Support Matrix

| Format | Core Install | Optional Install | Streaming |
|--------|-------------|------------------|-----------|
| JSON/JSONL | ✅ Included | - | ✅ JSONL only |
| CSV/TSV | ✅ Included | - | ✅ Yes |
| YAML | ✅ Included | - | ❌ No |
| XML | ✅ Included | - | ❌ No |
| API/URLs | ✅ Included | - | ❌ No |
| Parquet | ❌ | `pip install flatten-anything[parquet]` | ✅ Yes |
| Excel | ❌ | `pip install flatten-anything[excel]` | ❌ No |

## Quick Start

### Basic Usage
```python
from flatten_anything import flatten, ingest

# Load any supported file format
data = ingest('data.json')

# Flatten it (automatically handles single vs multiple records)
flat = flatten(data)
```

### Streaming Large Files
```python
# Process huge files in chunks
for chunk in ingest('massive.csv', stream=True, chunk_size=10000):
    flat_records = flatten(chunk)
    # Process chunk (e.g., write to database, analyze, etc.)
    process_records(flat_records)
```

### Real-world Example
```python
# Your horrible nested JSON
data = {
    "user": {
        "name": "John",
        "contacts": {
            "emails": ["john@example.com", "john@work.com"],
            "phones": {
                "home": "555-1234",
                "work": "555-5678"
            }
        }
    },
    "metrics": [1, 2, 3]
}

flat = flatten(data)
# {
#     'user.name': 'John',
#     'user.contacts.emails.0': 'john@example.com',
#     'user.contacts.emails.1': 'john@work.com',
#     'user.contacts.phones.home': '555-1234',
#     'user.contacts.phones.work': '555-5678',
#     'metrics.0': 1,
#     'metrics.1': 2,
#     'metrics.2': 3
# }
```

### Multiple Records Handling
```python
# CSV data with multiple records
users = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"}
]

# Default: flatten each record (records=True)
flat = flatten(users)
# [
#     {"name": "Alice", "age": 30, "city": "NYC"},
#     {"name": "Bob", "age": 25, "city": "LA"}
# ]

# Flatten as single structure (records=False)
flat = flatten(users, records=False)
# {
#     "0.name": "Alice", "0.age": 30, "0.city": "NYC",
#     "1.name": "Bob", "1.age": 25, "1.city": "LA"
# }
```

## Advanced Usage

### Integrate with pandas
```python
import pandas as pd

# Method 1: Load entire file
data = ingest('data.csv')
flat = flatten(data)
df = pd.DataFrame(flat)

# Method 2: Stream large files
dfs = []
for chunk in ingest('huge.csv', stream=True, chunk_size=5000):
    flat_chunk = flatten(chunk)
    dfs.append(pd.DataFrame(flat_chunk))
final_df = pd.concat(dfs, ignore_index=True)
```

### Control Empty Lists
```python
data = {"items": [], "count": 0}

# Preserve empty lists (default)
flatten(data, preserve_empty_lists=True)
# {"items": [], "count": 0}

# Remove empty lists
flatten(data, preserve_empty_lists=False)
# {"count": 0}
```

### Memory-Efficient Pipeline
```python
from pathlib import Path

# Process directory of large files without memory issues
for filepath in Path('data/').glob('*.csv'):
    for chunk in ingest(filepath, stream=True):
        flat = flatten(chunk)
        # Process and immediately discard to save memory
        send_to_database(flat)
```

## API Reference

### ingest()
```python
ingest(source, format=None, stream=False, chunk_size=5000, **kwargs)
```
- `source`: File path or URL to ingest
- `format`: Optional format override. Auto-detected if not specified
- `stream`: Enable streaming for large files (supported formats only)
- `chunk_size`: Records per chunk when streaming
- Returns: List of records or generator if streaming

### flatten()
```python
flatten(data, prefix="", preserve_empty_lists=True, records=True)
```
- `data`: Data structure to flatten
- `prefix`: Key prefix (used internally for recursion)
- `preserve_empty_lists`: Keep or remove empty lists
- `records`: Treat list as multiple records (True) or single structure (False)