from collections import deque
from pathlib import Path


def flatten(data, prefix: str = "", preserve_empty_lists: bool = True, 
            records: bool = True):
    """Transform nested data structures into flat key-value pairs using dot notation.

    Handles arbitrary nesting of dicts and lists, converting them into a flat
    dictionary where keys represent the path to each value. Useful for DataFrame
    conversion, API response normalization, and schema-agnostic data processing.

    Args:
        data: Input data structure (dict, list, or primitive value)
        prefix: Key prefix for recursion (typically left empty by caller)
        preserve_empty_lists: If True, empty lists are preserved as values.
                             If False, empty lists are removed from output.
        records: If True and data is a list, flatten each item separately.
                If False, flatten the entire structure as one.
                Default True (common case for CSV, JSONL, etc.)

    Returns:
        If records=True and data is list: List of flattened dicts (one per record)
        Otherwise: Dict with dot-notation keys mapping to leaf values

    Examples:
        >>> # Default behavior - treats lists as multiple records
        >>> flatten([{'name': 'Alice'}, {'name': 'Bob'}])
        [{'name': 'Alice'}, {'name': 'Bob'}]
        
        >>> # Single structure mode
        >>> flatten([{'name': 'Alice'}, {'name': 'Bob'}], records=False)
        {'0.name': 'Alice', '1.name': 'Bob'}

        >>> # Dict always flattens as single structure
        >>> flatten({'user': {'name': 'Alice', 'age': 30}})
        {'user.name': 'Alice', 'user.age': 30}

        >>> # Common pattern with ingest
        >>> data = ingest('users.csv')  # Returns list of records
        >>> flat = flatten(data)  # Automatically handles as records
    """
    # Handle record mode (default behavior for lists)
    if records and isinstance(data, list) and not prefix:
        # Flatten each item in the list separately
        return [flatten(item, preserve_empty_lists=preserve_empty_lists, 
                       records=False) for item in data]
    
    # Single structure flattening (original logic)
    if not prefix and not isinstance(data, (dict, list)):
        raise TypeError(
            f"Cannot flatten {type(data).__name__} at root level. "
            f"Expected dict or list. Got: {data!r}"
        )

    result = {}
    queue = deque([(prefix, data)])

    while queue:
        current_prefix, current_data = queue.popleft()

        if isinstance(current_data, dict):
            if not current_data:
                continue
            for k, v in current_data.items():
                k = str(k) if k is not None else "None"
                new_prefix = f"{current_prefix}{k}."
                queue.append((new_prefix, v))

        elif isinstance(current_data, list):
            if not current_data:
                if preserve_empty_lists:
                    final_key = current_prefix.rstrip(".")
                    if final_key:
                        result[final_key] = []
            else:
                for i, v in enumerate(current_data):
                    new_prefix = f"{current_prefix}{i}."
                    queue.append((new_prefix, v))

        else:
            final_key = current_prefix.rstrip(".")
            result[final_key] = current_data

    return result
