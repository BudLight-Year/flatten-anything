import json
import pandas as pd
import requests
import xmltodict
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Union
from .utils import check_optional_dependency


def ingest_json(filepath: Path) -> List[Dict[str, Any]]:
    """
    Ingest a json/jsonl file and convert into a list of dictionaries

    Args:
        filepath: source path to the json file

    Returns:
        List of dictionaries ready for flattening
    """
    try:
        with open(filepath, "r") as f:
            try:
                data = json.load(f)
                return [data] if isinstance(data, dict) else data
            except json.JSONDecodeError:
                f.seek(0)
                lines = [json.loads(line) for line in f if line.strip()]
                if not lines:
                    raise ValueError(f"No valid JSON found in {filepath}")
                return lines
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON syntax: {e}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not valid UTF-8 text")


def ingest_csv(filepath: Path, **kwargs) -> List[Dict[str, Any]]:
    """
    Ingest a csv file and read into a list of dictionaries


    Args:
        filepath: source path to the csv file
        **kwargs: additonal arguments for pd.read_csv()

    Returns:
        List of dictionaries ready for flattening
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        return df.to_dict("records")
    except pd.errors.EmptyDataError:
        return []
    except pd.errors.ParserError as e:
        raise ValueError(f"Malformed CSV: {e}")


def ingest_parquet(filepath: Path) -> List[Dict[str, Any]]:
    """
    Ingest a parquet file and read into a list of dictionaries.

    Args:
        filepath: Path object (already validated by ingest())

    Returns:
        List of dictionaries ready for flattening

    Note:
        Requires optional dependency: pip install flatten-anything[parquet]
    """
    check_optional_dependency("pyarrow", "parquet")
    try:
        df = pd.read_parquet(filepath)
        return df.to_dict("records")
    except Exception as e:
        if "parquet" in str(e).lower():
            raise ValueError(f"Invalid Parquet file: {e}")
        raise


def ingest_api(
    url: str,
    headers: Dict[str, str] = None,
    params: Dict[str, Any] = None,
    timeout: int = 30,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Read from an api endpoint and convert into a list of dictionaries

    Args:
        url         : Endpoint for the api
        headers     : Headers for the api request
        params      : Query parameters for the endpoint

    Returns:
        List of dictionaries ready for flattening
    """
    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=timeout, **kwargs
        )
        response.raise_for_status()
        data = response.json()
        return [data] if isinstance(data, dict) else data
    except requests.RequestException as e:
        raise ValueError(f"API request failed: {e}")
    except json.JSONDecodeError:
        raise ValueError(f"API response is not valid JSON")


def ingest_excel(filepath: Path, sheet_name=0, **kwargs) -> List[Dict[str, Any]]:
    """
    Ingest an excel file and read into a list of dictionaries.

    Args:
        filepath: Path object (already validated by ingest())
        sheet_name: Sheet name or index to read from
        **kwargs: Additional arguments for pd.read_excel()

    Returns:
        List of dictionaries ready for flattening

    Note:
        Requires optional dependency: pip install flatten-anything[excel]
    """
    check_optional_dependency("openpyxl", "excel")
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
        return df.to_dict("records")
    except ValueError as e:
        if "worksheet" in str(e).lower() or "sheet" in str(e).lower():
            with pd.ExcelFile(filepath) as xls:
                sheets = xls.sheet_names
            raise ValueError(
                f"Sheet '{sheet_name}' not found. " f"Available sheets: {sheets}"
            )
        raise ValueError(f"Invalid Excel file: {e}")


def ingest_yaml(filepath: Path) -> List[Dict[str, Any]]:
    """
    Ingest yaml file and read into a list of dictionaries

    Args:
        filepath: Path to the yaml file

    Returns:
        List of dictionaries ready for flattening
    """
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
            return [data] if isinstance(data, dict) else data
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}")
    except UnicodeDecodeError:
        raise ValueError(f"YAML file is not valid UTF-8")


def ingest_xml(filepath: Path) -> List[Dict[str, Any]]:
    """
    Ingest an xml file and parse into a list of dictionaries

    Args:
        filepath: Path to the xml file

    Returns:
        List of dictionaries ready for flattening
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()

            if content.strip().startswith("<!DOCTYPE html"):
                raise ValueError("File appears to be HTML, not XML")
            data = xmltodict.parse(content)
            return [data]
    except Exception as e:
        if "not well-formed" in str(e):
            raise ValueError(f"Invalid XML structure: {e}")
        raise ValueError(f"Failed to parse XML: {e}")


def ingest(source: str | Path, format: str = None, **kwargs) -> List[Dict[str, Any]]:
    """
    Universal ingestion function that auto-detects format with centralized validation.

    Args:
        source: File path or URL
        format: Optional format override ('json', 'csv', etc.)
        **kwargs: Format-specific options

    Returns:
        List of dictionaries ready for flattening
    """
    source_str = str(source)

    # Handle URLs/APIs
    if source_str.startswith(("http://", "https://")):
        format = format or "api"
    else:
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
            return []

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
        "api": ingest_api,
        "excel": ingest_excel,
        "yaml": ingest_yaml,
        "xml": ingest_xml,
    }

    if format not in ingestors:
        raise ValueError(
            f"Unsupported format: {format}. " f"Supported: {list(ingestors.keys())}"
        )

    if format == "api":
        return ingestors[format](source_str, **kwargs)
    else:
        return ingestors[format](source_path, **kwargs)
