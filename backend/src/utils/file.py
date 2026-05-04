import tempfile
from pathlib import Path


def get_temp_file_path(prefix: str = "gymbo_", suffix: str = "") -> Path:
    """
    Create a temporary file path without actually creating the file.

    Args:
        prefix: Prefix for the temporary file name
        suffix: Suffix/extension for the file (e.g., '.mp4', '.json')
        directory: Optional directory to create the temp file in

    Returns:
        Full path to the temporary file
    """
    return Path(
        tempfile.mktemp(prefix=prefix, suffix=suffix, dir=tempfile.gettempdir())
    )
