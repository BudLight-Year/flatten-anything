"""
JSON and JSONL format ingestion with optional streaming support.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Generator


def ingest_json(
    filepath: Path, 
    stream: bool = False,
    chunk_size: int = 1000, 
    **kwargs
) -> List[Dict[str, Any]] | Generator[List[Dict[str, Any]], None, None]:
    """
    Ingest JSON or JSONL file and convert to list of dictionaries.
    
    Args:
        filepath: Path to the JSON/JSONL file
        stream: If True, returns generator yielding chunks of records.
                Only supported for JSONL files, not regular JSON.
                If False, returns list of all records.
        chunk_size: Number of records per chunk when streaming. Ignored if stream=False.
        **kwargs: Reserved for future use
    
    Returns:
        If stream=False: List of dictionaries
        If stream=True: Generator yielding lists of dictionaries in chunks (JSONL only)
    
    Raises:
        ValueError: If JSON is malformed, cannot be parsed, or if streaming 
                   is requested for regular JSON files
        FileNotFoundError: If filepath does not exist
        NotImplementedError: If stream=True for regular JSON files
        
    Examples:
        >>> data = ingest_json('data.json')
        >>> len(data)
        100
        
        >>> for chunk in ingest_json('large.jsonl', stream=True, chunk_size=500):
        ...     print(f"Processing {len(chunk)} records")
        Processing 500 records
        Processing 500 records
    """
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {filepath}")
    
    if filepath.stat().st_size == 0:
        return [] if not stream else iter([[]])
    
    is_jsonl = _is_jsonl(filepath)
    
    if stream and not is_jsonl:
        raise NotImplementedError(
            "Streaming is only supported for JSONL files. "
            "Regular JSON files must be loaded entirely into memory. "
            "Consider converting to JSONL format for streaming support."
        )
    
    if is_jsonl:
        if stream:
            return _stream_jsonl(filepath, chunk_size)
        else:
            return _load_jsonl(filepath)
    else:
        return _load_json(filepath)


def _is_jsonl(filepath: Path) -> bool:
    """
    Detect if file is JSONL format by checking extension and content.
    
    Args:
        filepath: Path to check
        
    Returns:
        True if file appears to be JSONL format
    """
    if filepath.suffix.lower() in ['.jsonl', '.ndjson']:
        return True
    
    if filepath.suffix.lower() != '.json':
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines_checked = 0
            for line in f:
                if not line.strip():
                    continue
                    
                try:
                    json.loads(line)
                    lines_checked += 1
                    
                    if lines_checked == 2:
                        return True
                except json.JSONDecodeError:
                    return False
                    
            return False
            
    except (UnicodeDecodeError, IOError):
        return False


def _load_json(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load entire JSON file into memory.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        List of dictionaries
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if data is None:
            return []
        elif isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            if not data:
                return []
            if isinstance(data[0], dict):
                return data
            # Wrap primitive list items in dicts
            return [{"value": item} for item in data]
        else:
            # Wrap primitive value
            return [{"value": data}]
            
    except json.JSONDecodeError as e:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        if e.lineno and e.lineno <= len(lines):
            error_line = lines[e.lineno - 1][:100]
            raise ValueError(
                f"Invalid JSON syntax at line {e.lineno}: {e.msg}\n"
                f"Problem line: {error_line}"
            )
        raise ValueError(f"Invalid JSON syntax: {e}")
        
    except UnicodeDecodeError as e:
        raise ValueError(
            f"File is not valid UTF-8 text. "
            f"Error at byte {e.start}: {e.reason}"
        )


def _load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load entire JSONL file into memory.
    
    Args:
        filepath: Path to JSONL file
    
    Returns:
        List of dictionaries, one per line
    """
    records = []
    line_num = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                    
                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        records.append(record)
                    else:
                        # Wrap non-dict values
                        records.append({"value": record})
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON at line {line_num}: {e.msg}\n"
                        f"Content: {line[:100]}..."
                    )
                    
        return records
        
    except UnicodeDecodeError as e:
        raise ValueError(
            f"File is not valid UTF-8 text at line {line_num}. "
            f"Error at byte {e.start}: {e.reason}"
        )


def _stream_jsonl(filepath: Path, chunk_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream JSONL file in chunks for memory efficiency.
    
    Args:
        filepath: Path to JSONL file
        chunk_size: Number of records per chunk
    
    Yields:
        Lists of dictionaries, each list containing up to chunk_size records
    """
    chunk = []
    line_num = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                    
                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        chunk.append(record)
                    else:
                        # Wrap non-dict values
                        chunk.append({"value": record})
                    
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON at line {line_num}: {e.msg}\n"
                        f"Content: {line[:100]}..."
                    )
            
            if chunk:
                yield chunk
                
    except UnicodeDecodeError as e:
        raise ValueError(
            f"File is not valid UTF-8 text at line {line_num}. "
            f"Error at byte {e.start}: {e.reason}"
        )
