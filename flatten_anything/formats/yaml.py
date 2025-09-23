"""
YAML format ingestion for configuration and data files.
"""
import yaml
from pathlib import Path
from typing import List, Dict, Any


def ingest_yaml(
    filepath: Path, 
    stream: bool = False,
    chunk_size: int = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Ingest YAML file and parse into list of dictionaries.
    
    Args:
        filepath: Path to the YAML file
        stream: If True, raises NotImplementedError as YAML doesn't support streaming
        **kwargs: Additional arguments passed to yaml.safe_load()
                 (e.g., Loader for custom loading behavior)
    
    Returns:
        List containing parsed YAML data (single dict or list of dicts)
    
    Raises:
        ValueError: If YAML syntax is invalid or cannot be parsed
        FileNotFoundError: If filepath does not exist
        NotImplementedError: If stream=True is requested
        
    Examples:
        >>> data = ingest_yaml('config.yaml')
        >>> data[0]['database']['host']
        'localhost'
        
        >>> # Multi-document YAML
        >>> data = ingest_yaml('multiple.yaml')
        >>> len(data)  # Each document becomes a list item
        3
        
    Note:
        Streaming is not supported for YAML files as they are typically small
        configuration files and lack standardized streaming parsers. For large
        data files, consider using JSONL or Parquet format instead.
    """
    if stream:
        raise NotImplementedError(
            "Streaming is not supported for YAML files. "
            "YAML files are typically small configuration files that don't require streaming. "
            "For large data files, consider using JSONL or Parquet format instead."
        )
    
    return _load_yaml(filepath, **kwargs)


def _load_yaml(filepath: Path, **kwargs) -> List[Dict[str, Any]]:
    """
    Load and parse YAML file into dictionary structure.
    
    Args:
        filepath: Path to the YAML file
        **kwargs: Additional arguments for yaml.safe_load()
    
    Returns:
        List of dictionaries from parsed YAML
    """
    if not filepath.exists():
        raise FileNotFoundError(f"YAML file not found: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {filepath}")
    
    if filepath.suffix.lower() not in ['.yaml', '.yml']:
        raise ValueError(
            f"File extension '{filepath.suffix}' is not a recognized YAML format. "
            f"Expected .yaml or .yml"
        )
    
    if filepath.stat().st_size == 0:
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if not content.strip() or all(
                line.strip().startswith('#') or not line.strip() 
                for line in content.split('\n')
            ):
                return []
            
            f.seek(0)
            
            # Multi-document YAML support
            if '\n---\n' in content or content.startswith('---\n'):
                documents = []
                for doc in yaml.safe_load_all(f):
                    if doc is not None:
                        if isinstance(doc, dict):
                            documents.append(doc)
                        elif isinstance(doc, list):
                            if doc and isinstance(doc[0], dict):
                                documents.extend(doc)
                            else:
                                # Wrap primitive list items
                                documents.extend([{"value": item} for item in doc])
                        else:
                            documents.append({"value": doc})
                return documents if documents else []
            else:
                # Single document YAML
                data = yaml.safe_load(f)
                
                if data is None:
                    return []
                elif isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    if not data:
                        return []
                    if isinstance(data[0], dict):
                        return data
                    # Wrap primitive list items
                    return [{"value": item} for item in data]
                else:
                    return [{"value": data}]
                    
    except yaml.YAMLError as e:
        error_msg = str(e)
        
        if "could not find expected" in error_msg.lower():
            raise ValueError(
                f"Invalid YAML indentation or structure: {e}. "
                f"Check that indentation is consistent (spaces only, no tabs)."
            )
        elif "mapping values are not allowed" in error_msg.lower():
            raise ValueError(
                f"Invalid YAML syntax: {e}. "
                f"Check for missing colons or incorrect spacing after colons."
            )
        elif "duplicate key" in error_msg.lower():
            raise ValueError(
                f"Duplicate keys found in YAML: {e}. "
                f"Each key must be unique within its scope."
            )
        else:
            import re
            line_match = re.search(r'line (\d+)', error_msg)
            if line_match:
                line_num = line_match.group(1)
                lines = content.split('\n')
                if int(line_num) <= len(lines):
                    problem_line = lines[int(line_num) - 1]
                    raise ValueError(
                        f"Invalid YAML syntax at line {line_num}: {e}\n"
                        f"Problem line: {problem_line}"
                    )
            
            raise ValueError(f"Invalid YAML syntax: {e}")
            
    except UnicodeDecodeError as e:
        raise ValueError(
            f"YAML file is not valid UTF-8 text. "
            f"Error at byte {e.start}: {e.reason}"
        )
        
    except Exception as e:
        if "yaml" in str(e).lower():
            raise ValueError(f"Failed to parse YAML: {e}")
        raise ValueError(f"Unexpected error parsing YAML: {e}")
