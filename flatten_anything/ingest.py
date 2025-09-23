"""
Universal data ingestion with automatic format detection.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Generator
from .formats import (
    ingest_csv,
    ingest_json,
    ingest_parquet,
    ingest_excel,
    ingest_xml,
    ingest_yaml,
    ingest_api
)


def ingest(
    source: str | Path,
    format: str | None = None,
    stream: bool = False,
    chunk_size: int = 5000,
    **kwargs
) -> List[Dict[str, Any]] | Generator[List[Dict[str, Any]], None, None]:
    """
    Universal ingestion function that auto-detects format with centralized validation.

    Args:
        source: File path or URL
        format: Optional format override ('json', 'csv', etc.)
        stream: If True, returns generator for supported formats
        chunk_size: Number of records per chunk when streaming
        **kwargs: Format-specific options

    Returns:
        List of dictionaries ready for flattening, or generator if streaming
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unsupported or file is invalid
        PermissionError: If file cannot be read
        NotImplementedError: If streaming requested for unsupported format
    """
    source_str = str(source)

    # Handle URLs/APIs
    if source_str.startswith(("http://", "https://")):
        format = format or "api"
        return ingest_api(source_str, stream=stream, chunk_size=chunk_size, **kwargs)
    
    # Handle files
    source_path = Path(source)

    # File validation
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path.absolute()}")

    if not source_path.is_file():
        raise ValueError(f"Not a file: {source_path}")

    if not os.access(source_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {source_path}")

    if source_path.stat().st_size == 0:
        return [] if not stream else iter([[]])

    # Auto-detect format from extension
    if format is None:
        ext = source_path.suffix.lower()
        format_map = {
            ".json": "json",
            ".jsonl": "json",
            ".csv": "csv",
            ".parquet": "parquet",
            ".parq": "parquet",
            ".xlsx": "excel",
            ".xls": "excel",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
        }
        format = format_map.get(ext)

        if format is None:
            raise ValueError(
                f"Unknown file extension '{ext}'.\n"
                f"Specify format explicitly: ingest(file, format='json')"
            )

    # Route to appropriate ingester
    ingestors = {
        "json": ingest_json,
        "csv": ingest_csv,
        "parquet": ingest_parquet,
        "excel": ingest_excel,
        "yaml": ingest_yaml,
        "xml": ingest_xml,
    }

    if format not in ingestors:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported: {list(ingestors.keys()) + ['api']}"
        )

    return ingestors[format](source_path, stream=stream, chunk_size=chunk_size, **kwargs)
