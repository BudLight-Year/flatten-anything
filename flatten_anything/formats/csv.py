"""
CSV format ingestion with optional streaming support.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Generator


def ingest_csv(filepath: Path, stream: bool = False, 
               chunk_size: int = 5000, **kwargs) -> List[Dict[str, Any]] | Generator[List[Dict[str, Any]], None, None]:
    """
    Ingest CSV file and convert to list of dictionaries.
    
    Args:
        filepath: Path to the CSV file
        stream: If True, returns generator yielding chunks of records.
                If False, returns list of all records.
        chunk_size: Number of rows per chunk when streaming. Ignored if stream=False.
        **kwargs: Additional arguments passed to pandas.read_csv()
    
    Returns:
        If stream=False: List of dictionaries, one per row
        If stream=True: Generator yielding lists of dictionaries in chunks
    
    Raises:
        ValueError: If CSV file is malformed or cannot be parsed
        FileNotFoundError: If filepath does not exist
        
    Examples:
        >>> data = ingest_csv('data.csv')
        >>> len(data)
        1000
        
        >>> for chunk in ingest_csv('large.csv', stream=True, chunk_size=500):
        ...     print(f"Processing {len(chunk)} records")
        Processing 500 records
        Processing 500 records
    """
    if stream:
        return _stream_csv(filepath, chunk_size, **kwargs)
    else:
        return _load_csv(filepath, **kwargs)


def _load_csv(filepath: Path, **kwargs) -> List[Dict[str, Any]]:
    """
    Load entire CSV into memory.
    
    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv()
    
    Returns:
        List of dictionaries representing all rows
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        return df.to_dict("records")
    except pd.errors.EmptyDataError:
        return []
    except pd.errors.ParserError as e:
        raise ValueError(f"Malformed CSV: {e}")


def _stream_csv(filepath: Path, chunk_size: int = 5000, 
                **kwargs) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream CSV file in chunks for memory efficiency.
    
    Args:
        filepath: Path to CSV file
        chunk_size: Number of rows per chunk
        **kwargs: Additional arguments for pd.read_csv()
    
    Yields:
        Lists of dictionaries, each list containing chunk_size rows
    """
    try:
        reader = pd.read_csv(filepath, chunksize=chunk_size, **kwargs)
        
        for chunk_df in reader:
            chunk_records = chunk_df.to_dict('records')
            yield chunk_records
            
    except pd.errors.EmptyDataError:
        yield []
    except pd.errors.ParserError as e:
        raise ValueError(f"Malformed CSV at chunk: {e}")
    finally:
        if 'reader' in locals() and hasattr(reader, 'close'):
            reader.close()
