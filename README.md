# Flatten Anything 🔨

*Stop writing custom parsers for every data format. Flatten anything.*

[![PyPI](https://img.shields.io/pypi/v/flatten-anything?color=blue)](https://pypi.org/project/flatten-anything/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
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

**It just works.** No matter what garbage is in your file.

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

### What's Included

| Format | Core Install | Optional Install |
|--------|-------------|------------------|
| JSON/JSONL | ✅ Included | - |
| CSV/TSV | ✅ Included | - |
| YAML | ✅ Included | - |
| XML | ✅ Included | - |
| API/URLs | ✅ Included | - |
| Parquet | ❌ | `pip install flatten-anything[parquet]` |
| Excel | ❌ | `pip install flatten-anything[excel]` |

The core package is kept lightweight (~35MB) while Parquet and Excel support can add ~100MB+ if you need them.

## Quick Start

### Flatten nested JSON
```python
from flatten_anything import flatten, ingest

# Load any supported file format
data = ingest('deeply_nested.json')

# Flatten it
flat = flatten(data)

# {'user.name': 'John', 'user.address.city': 'NYC', 'user.scores.0': 100}
```

### Real-world example
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

### Works with any format
```python
# JSON
data = ingest('data.json')

# CSV  
data = ingest('data.csv')

# Parquet
data = ingest('data.parquet')

# Excel
data = ingest('data.xlsx')

# XML
data = ingest('data.xml')

# YAML
data = ingest('config.yaml')

# All flatten the same way
flat = flatten(data)
```

## Supported Formats

| Format | Extensions | Status |
|--------|-----------|---------|
| JSON | `.json` | ✅ Fully supported |
| JSONL | `.jsonl` | ✅ Fully supported |
| CSV | `.csv`, `.tsv` | ✅ Fully supported |
| Parquet | `.parquet`, `.parq` | ✅ Fully supported |
| Excel | `.xlsx`, `.xls` | ✅ Fully supported |
| XML | `.xml` | ✅ Fully supported |
| YAML | `.yaml`, `.yml` | ✅ Fully supported |

## Why Flatten Anything?

- **Zero configuration** - No schemas, no options, just works
- **Production ready** - Handle nulls, mixed types, empty arrays without crashing
- **Actually tested** - On real messy production data, not toy examples
- **Minimal dependencies** - Just the essentials (pandas, pyyaml, etc.)
- **One job** - Flatten data. That's it. No bloat.

## Advanced Usage

### Control the output structure
```python
# Have multiple records? Each gets flattened
data = ingest('multiple_records.json')  # List of records
flattened_records = [flatten(record) for record in data]
```

### Integrate with pandas
```python
import pandas as pd

# Flatten and convert to DataFrame
data = ingest('nested_data.json')
flat = flatten(data)
df = pd.DataFrame([flat])
```

### Pipeline ready
```python
# Chain with your existing workflow
for filename in Path('data/').glob('*.json'):
    data = ingest(filename)
    flat = flatten(data)
    # Your analysis here
    process_data(flat)
```

## Use Cases

- **Data Engineering**: Normalize data lakes with mixed formats
- **ETL Pipelines**: Consistent structure regardless of source format  
- **Data Analysis**: Flatten nested JSON APIs into DataFrames
- **Log Processing**: Convert nested log formats to flat structures
- **Config Management**: Flatten complex YAML/JSON configs for validation

## FAQ

**Q: What happens with null values?**  
A: They're preserved. `{'a': {'b': null}}` becomes `{'a.b': None}`

**Q: What about empty arrays?**  
A: They're kept. `{'items': []}` becomes `{'items': []}`

**Q: Can it handle huge files?**  
A: Currently loads into memory. Streaming support coming in v1.1.

**Q: What if my JSON has inconsistent structure?**  
A: It still works. Missing keys are simply not included in the output.

## Contributing

Found a bug? File that doesn't flatten? Open an issue with a sample file.

PRs welcome, especially for:
- More file formats
- Performance improvements  
- Edge case handling

## License

MIT - Use it however you want.

## Roadmap

- ✅ v1.0 - Core flattening for common formats
- 🔄 v1.1 - Streaming support for large files
- 📋 v1.2 - API endpoint support with pagination
- 🔮 v1.3 - HDF5 and scientific formats

---

*Built with frustration at writing the same parsing code for the 100th time.*