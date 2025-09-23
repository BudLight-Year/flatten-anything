"""
XML format ingestion for structured XML files.
"""
import xmltodict
from pathlib import Path
from typing import List, Dict, Any


def ingest_xml(
    filepath: Path, 
    stream: bool = False,
    chunk_size: int = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Ingest XML file and parse into list of dictionaries.
    
    Args:
        filepath: Path to the XML file
        stream: If True, raises NotImplementedError as XML doesn't support streaming
        **kwargs: Additional arguments passed to xmltodict.parse()
                 (e.g., process_namespaces, namespaces, dict_constructor)
    
    Returns:
        List containing single dictionary of parsed XML structure
    
    Raises:
        ValueError: If XML structure is invalid, file is HTML, or cannot be parsed
        FileNotFoundError: If filepath does not exist
        NotImplementedError: If stream=True is requested
        
    Examples:
        >>> data = ingest_xml('config.xml')
        >>> flat = flatten(data[0])
        
        >>> # With namespace handling
        >>> data = ingest_xml('data.xml', process_namespaces=True)
        
    Note:
        Streaming is not supported for XML files due to their hierarchical 
        structure lacking natural record boundaries. For large XML files,
        consider converting to JSONL or CSV format for streaming support.
    """
    if stream:
        raise NotImplementedError(
            "Streaming is not supported for XML files. "
            "XML's hierarchical structure doesn't have natural record boundaries. "
            "Consider converting to JSONL or CSV format for streaming support."
        )
    
    return _load_xml(filepath, **kwargs)


def _load_xml(filepath: Path, **kwargs) -> List[Dict[str, Any]]:
    """
    Load and parse XML file into dictionary structure.
    
    Args:
        filepath: Path to the XML file
        **kwargs: Additional arguments for xmltodict.parse()
    
    Returns:
        List containing single dictionary of parsed XML
    """
    # Validate file exists
    if not filepath.exists():
        raise FileNotFoundError(f"XML file not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {filepath}")
    
    # Check file extension
    if filepath.suffix.lower() not in ['.xml', '.xsd', '.xsl', '.xslt']:
        raise ValueError(
            f"File extension '{filepath.suffix}' is not a recognized XML format. "
            f"Expected .xml, .xsd, .xsl, or .xslt"
        )
    
    # Check if file is empty
    if filepath.stat().st_size == 0:
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Quick validation checks
        content_start = content[:500].strip().lower()
        
        # Check if it's HTML instead of XML
        if content_start.startswith("<!doctype html") or content_start.startswith("<html"):
            raise ValueError(
                "File appears to be HTML, not XML. "
                "HTML parsing is not supported."
            )
        
        # Check for completely empty content
        if not content.strip():
            return []
        
        # Parse XML
        data = xmltodict.parse(content, **kwargs)
        
        # xmltodict returns None for empty XML
        if data is None:
            return []
        
        # Ensure we return a list
        return [data]
        
    except UnicodeDecodeError as e:
        raise ValueError(
            f"File is not valid UTF-8 text. "
            f"Error at byte {e.start}: {e.reason}"
        )
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Provide specific error messages
        if "not well-formed" in error_msg:
            # Try to extract line number from error
            import re
            line_match = re.search(r'line (\d+)', error_msg)
            if line_match:
                line_num = line_match.group(1)
                raise ValueError(
                    f"Invalid XML structure at line {line_num}. "
                    f"Check for unclosed tags, invalid characters, or missing quotes."
                )
            raise ValueError(f"Invalid XML structure: {e}")
            
        elif "undefined entity" in error_msg:
            raise ValueError(
                f"XML contains undefined entities: {e}. "
                f"Consider using process_namespaces=False or defining entities."
            )
            
        elif "syntax error" in error_msg:
            raise ValueError(
                f"XML syntax error: {e}. "
                f"Check for malformed tags or invalid characters."
            )
            
        elif "encoding" in error_msg:
            raise ValueError(
                f"XML encoding error: {e}. "
                f"File may use a different encoding than UTF-8."
            )
            
        elif "xmltodict" in str(e):
            raise ValueError(f"Failed to parse XML: {e}")
            
        # Re-raise unexpected errors
        raise ValueError(f"Unexpected error parsing XML: {e}")
