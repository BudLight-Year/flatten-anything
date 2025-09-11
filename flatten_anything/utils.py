"""
Utility functions for FlattenAnything
"""


def check_optional_dependency(package_name: str, feature_name: str):
    """
    Check if optional dependency is installed.

    Args:
        package_name: Name of the package to import
        feature_name: Feature name for error message (e.g., 'parquet', 'excel')

    Raises:
        ImportError: With helpful installation instructions
    """
    try:
        __import__(package_name)
    except ImportError:
        raise ImportError(
            f"\n"
            f"{feature_name.title()} support requires '{package_name}'.\n"
            f"Install with one of:\n"
            f"  pip install flatten-anything[{feature_name}]\n"
            f"  pip install flatten-anything[all]\n"
            f"  pip install {package_name}"
        )
