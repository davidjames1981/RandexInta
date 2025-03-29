import os
from pathlib import Path

def get_watch_path(*paths):
    """
    Constructs a full path by joining the root watch folder with the given path segments.
    Creates the directory if it doesn't exist.
    
    Args:
        *paths: Variable number of path segments to join with the root watch folder
        
    Returns:
        str: Full path including the root watch folder
    """
    root_folder = os.getenv('WATCH_FOLDER')
    if not root_folder:
        raise ValueError("WATCH_FOLDER environment variable is not set")
    
    # Convert to Path object for proper path handling
    # Replace backslashes with forward slashes for consistency
    root_folder = root_folder.replace('\\', '/')
    full_path = Path(root_folder)
    
    # Join with additional path segments
    for path in paths:
        if path:
            # Ensure path segment uses forward slashes
            path = str(path).replace('\\', '/')
            full_path = full_path / path
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(full_path, exist_ok=True, mode=0o777)  # Full permissions for Docker compatibility
    except PermissionError as e:
        # Log error but don't fail - the directory might already exist in Docker volume
        import logging
        logger = logging.getLogger('path_utils')
        logger.warning(f"Could not create directory {full_path}: {e}")
    
    # Always return path with forward slashes
    return str(full_path).replace('\\', '/') 