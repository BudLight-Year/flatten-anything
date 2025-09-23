"""
Excel format ingestion for .xlsx and .xls files.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from ..utils import check_optional_dependency


def ingest_excel(
    filepath: Path, 
    stream: bool = False,
    sheet_name: str | int = 0,
    chunk_size: int = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Ingest Excel file and convert to list of dictionaries.
    
    Args:
        filepath: Path to the Excel file (.xlsx or .xls)
        stream: If True, raises NotImplementedError as Excel doesn't support efficient streaming
        sheet_name: Name or index of sheet to read. Default 0 (first sheet).
                   Use None to read all sheets (returns dict of sheet_name -> records).
        **kwargs: Additional arguments passed to pandas.read_excel()
                 (e.g., skiprows, usecols, dtype, na_values, parse_dates)
    
    Returns:
        List of dictionaries, one per row in the Excel sheet.
        If sheet_name=None, returns dict with sheet names as keys.
    
    Raises:
        ValueError: If Excel file is invalid, corrupted, or specified sheet doesn't exist
        ImportError: If openpyxl is not installed
        FileNotFoundError: If filepath does not exist
        NotImplementedError: If stream=True is requested
        
    Examples:
        >>> data = ingest_excel('report.xlsx')
        >>> len(data)
        100
        
        >>> data = ingest_excel('report.xlsx', sheet_name='Sales')
        >>> data[0]['revenue']
        50000
        
        >>> all_sheets = ingest_excel('workbook.xlsx', sheet_name=None)
        >>> list(all_sheets.keys())
        ['Sheet1', 'Sheet2', 'Sales']
        
    Note:
        Streaming is not supported for Excel files. Excel's row-based structure
        doesn't provide efficient record streaming. For large datasets, 
        export to CSV or Parquet format first.
        
        Requires optional dependency: pip install flatten-anything[excel]
    """
    if stream:
        raise NotImplementedError(
            "Streaming is not supported for Excel files. "
            "Excel's row-based structure doesn't provide efficient record streaming. "
            "For large datasets, consider exporting to CSV format first: "
            "pd.read_excel('file.xlsx').to_csv('file.csv', index=False)"
        )
    
    # Check for required dependency
    check_optional_dependency("openpyxl", "excel")
    
    # Validate file exists and is readable
    if not filepath.exists():
        raise FileNotFoundError(f"Excel file not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {filepath}")
    
    # Check file extension
    if filepath.suffix.lower() not in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
        raise ValueError(
            f"File extension '{filepath.suffix}' is not a recognized Excel format. "
            f"Expected .xlsx, .xls, .xlsm, or .xlsb"
        )
    
    try:
        # Handle reading all sheets
        if sheet_name is None:
            dfs = pd.read_excel(filepath, sheet_name=None, **kwargs)
            return {
                sheet: df.to_dict("records") 
                for sheet, df in dfs.items()
            }
        
        # Read specific sheet
        df = pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
        
        # Handle empty DataFrame
        if df.empty:
            return []
        
        # Convert to list of dicts
        records = df.to_dict("records")
        
        # Clean up NaN values to None for consistency
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return records
        
    except ValueError as e:
        error_msg = str(e).lower()
        
        # Provide helpful error for missing sheet
        if "worksheet" in error_msg or "sheet" in error_msg:
            try:
                with pd.ExcelFile(filepath) as xls:
                    available_sheets = xls.sheet_names
                    
                if isinstance(sheet_name, int):
                    raise ValueError(
                        f"Sheet index {sheet_name} is out of range. "
                        f"File has {len(available_sheets)} sheet(s): {available_sheets}"
                    )
                else:
                    raise ValueError(
                        f"Sheet '{sheet_name}' not found. "
                        f"Available sheets: {available_sheets}"
                    )
            except Exception:
                # If we can't read sheet names, use original error
                raise ValueError(f"Cannot read sheet '{sheet_name}': {e}")
        
        # Check for corrupted file
        elif "corrupt" in error_msg or "invalid" in error_msg:
            raise ValueError(
                f"Excel file appears to be corrupted or invalid: {e}. "
                f"Try opening and re-saving the file in Excel."
            )
        
        # Generic Excel error
        raise ValueError(f"Failed to read Excel file: {e}")
        
    except PermissionError:
        raise ValueError(
            f"Permission denied reading {filepath}. "
            f"Make sure the file is not open in Excel."
        )
    
    except Exception as e:
        # Catch-all for unexpected errors
        if "openpyxl" in str(e):
            raise ImportError(
                "Excel support requires openpyxl. "
                "Install with: pip install flatten-anything[excel]"
            )
        raise ValueError(f"Unexpected error reading Excel file: {e}")
