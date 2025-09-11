from collections import deque
from pathlib import Path


def flatten(data, prefix: str = "", preserve_empty_lists: bool = True):
    """Transform nested data structures into flat key-value pairs using dot notation.

    Handles arbitrary nesting of dicts and lists, converting them into a flat
    dictionary where keys represent the path to each value. Useful for DataFrame
    conversion, API response normalization, and schema-agnostic data processing.

    Args:
        data: Input data structure (dict, list, or primitive value)
        prefix: Key prefix for recursion (typically left empty by caller)
        preserve_empty_lists: If True, empty lists are preserved as values.
                             If False, empty lists are removed from output.

    Returns:
        Dict with dot-notation keys mapping to leaf values

    Examples:
        >>> flatten({'user': {'name': 'Alice', 'age': 30}})
        {'user.name': 'Alice', 'user.age': 30}

        >>> flatten({'items': [{'id': 1}, {'id': 2}]})
        {'items.0.id': 1, 'items.1.id': 2}

        >>> flatten([10, 20, 30])
        {'0': 10, '1': 20, '2': 30}

        >>> flatten({'tags': []})
        {'tags': []}  # With preserve_empty_lists=True

        >>> flatten({'tags': []}, preserve_empty_lists=False)
        {}  # With preserve_empty_lists=False
    """
    if not prefix and not isinstance(data, (dict, list)):
        raise TypeError(
            f"Cannot flatten {type(data).__name__} at root level"
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
                # else: skip empty lists (don't add to results)
            else:
                for i, v in enumerate(current_data):
                    new_prefix = f"{current_prefix}{i}."
                    queue.append((new_prefix, v))

        else:
            final_key = current_prefix.rstrip(".")
            result[final_key] = current_data

    return result
