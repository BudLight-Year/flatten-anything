"""
Parquet format ingestion with optional streaming support.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Generator
from ..utils import check_optional_dependency


def ingest_parquet(
    filepath: Path, 
    stream: bool = False,
    chunk_size: int = 5000, 
    **kwargs
) -> List[Dict[str, Any]] | Generator[List[Dict[str, Any]], None, None]:
    """
    Ingest Parquet file and convert to list of dictionaries.
    
    Args:
        filepath: Path to the Parquet file
        stream: If True, returns generator yielding chunks of records.
                If False, returns list of all records.
        chunk_size: Number of rows per chunk when streaming. Ignored if stream=False.
        **kwargs: Additional arguments passed to pyarrow.parquet.ParquetFile or pandas.read_parquet
                 (e.g., columns, filters, use_pandas_metadata)
    
    Returns:
        If stream=False: List of dictionaries
        If stream=True: Generator yielding lists of dictionaries in chunks
    
    Raises:
        ImportError: If pyarrow is not installed
        ValueError: If Parquet file is invalid, corrupted, or cannot be parsed
        FileNotFoundError: If filepath does not exist
        
    Examples:
        >>> data = ingest_parquet('data.parquet')
        >>> len(data)
        10000
        
        >>> # Read specific columns only
        >>> data = ingest_parquet('data.parquet', columns=['id', 'name'])
        
        >>> # Stream large file in chunks
        >>> for chunk in ingest_parquet('large.parquet', stream=True, chunk_size=1000):
        ...     print(f"Processing {len(chunk)} records")
        Processing 1000 records
        Processing 1000 records
        
    Note:
        Requires optional dependency: pip install flatten-anything[parquet]
    """
    # Check for required dependency
    check_optional_dependency("pyarrow", "parquet")
    
    # Validate file exists
    if not filepath.exists():
        raise FileNotFoundError(f"Parquet file not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {filepath}")
    
    # Check file extension
    if filepath.suffix.lower() not in ['.parquet', '.parq']:
        raise ValueError(
            f"File extension '{filepath.suffix}' is not a recognized Parquet format. "
            f"Expected .parquet or .parq"
        )
    
    # Check if file is empty
    if filepath.stat().st_size == 0:
        return [] if not stream else iter([[]])
    
    if stream:
        return _stream_parquet(filepath, chunk_size, **kwargs)
    else:
        return _load_parquet(filepath, **kwargs)


def _load_parquet(filepath: Path, **kwargs) -> List[Dict[str, Any]]:
    """
    Load entire Parquet file into memory using pandas.
    
    Args:
        filepath: Path to Parquet file
        **kwargs: Additional arguments for pandas.read_parquet
    
    Returns:
        List of dictionaries representing all rows
    """
    try:
        df = pd.read_parquet(filepath, **kwargs)
        
        # Handle empty DataFrame
        if df.empty:
            return []
        
        # Convert to records
        records = df.to_dict('records')
        
        # Clean up NaN values to None for consistency
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                    
        return records
        
    except ImportError as e:
        if "pyarrow" in str(e) or "fastparquet" in str(e):
            raise ImportError(
                "Parquet support requires pyarrow. "
                "Install with: pip install flatten-anything[parquet]"
            )
        raise
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "pyarrow" in error_msg or "fastparquet" in error_msg:
            raise ImportError(
                "Parquet support requires pyarrow. "
                "Install with: pip install flatten-anything"
            )
        
        # Specific error handling
        if "could not open parquet" in error_msg:
            raise ValueError(
                f"Cannot open Parquet file. File may be corrupted or incomplete. "
                f"Try regenerating the file."
            )
        elif "parquet magic bytes" in error_msg:
            raise ValueError(
                f"File is not a valid Parquet file. "
                f"It may be a different format with .parquet extension."
            )
        elif "schema" in error_msg:
            raise ValueError(
                f"Parquet schema error: {e}. "
                f"File may have inconsistent or corrupted schema."
            )
        elif any(x in error_msg for x in ["parquet", "arrow", "corrupt"]):
            raise ValueError(f"Invalid or corrupted Parquet file: {e}")
            
        # Re-raise unexpected errors
        raise


def _stream_parquet(
    filepath: Path, 
    chunk_size: int = 5000,
    **kwargs
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream Parquet file in chunks for memory efficiency.
    
    Uses PyArrow's native batch iteration for optimal performance.
    
    Args:
        filepath: Path to Parquet file
        chunk_size: Number of rows per batch
        **kwargs: Additional arguments for pyarrow.parquet.ParquetFile
    
    Yields:
        Lists of dictionaries, each list containing up to chunk_size rows
    """
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError(
            "Parquet streaming requires pyarrow. "
            "Install with: pip install flatten-anything[parquet]"
        )
    
    try:
        # Open Parquet file with PyArrow
        parquet_file = pq.ParquetFile(filepath, **kwargs)
        
        # Check if file is empty
        if parquet_file.metadata.num_rows == 0:
            yield []
            return
        
        # Stream in batches
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            # Convert Arrow batch to pandas DataFrame
            df = batch.to_pandas()
            
            # Convert to records
            chunk_records = df.to_dict('records')
            
            # Clean up NaN values
            for record in chunk_records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            yield chunk_records
            
    except FileNotFoundError:
        raise FileNotFoundError(f"Parquet file not found: {filepath}")
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Specific error handling for streaming
        if "could not open parquet" in error_msg:
            raise ValueError(
                f"Cannot open Parquet file for streaming. "
                f"File may be corrupted or incomplete."
            )
        elif "parquet magic bytes" in error_msg:
            raise ValueError(
                f"File is not a valid Parquet file format."
            )
        elif "out of memory" in error_msg or "memory" in error_msg:
            raise ValueError(
                f"Out of memory while streaming. "
                f"Try reducing chunk_size from {chunk_size} to a smaller value."
            )
        elif any(x in error_msg for x in ["parquet", "arrow", "corrupt"]):
            raise ValueError(f"Invalid or corrupted Parquet file: {e}")
            
        # Re-raise unexpected errors
        raise
