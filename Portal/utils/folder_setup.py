import os
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

def ensure_folders_exist():
    """
    Ensures all required folders for the application exist.
    Creates them if they don't exist.
    """
    try:
        # Get the root watch folder from environment
        watch_folder = os.getenv('WATCH_FOLDER')
        if not watch_folder:
            logger.error("WATCH_FOLDER environment variable is not set")
            return False

        # Define all required subfolders
        subfolders = {
            'inventory': os.getenv('INVENTORY_IMPORT_FOLDER', 'inventory'),
            'orders': os.getenv('ORDERS_IMPORT_FOLDER', 'orders'),
            'export': os.getenv('ORDERS_EXPORT_FOLDER', 'export'),
            'processed': os.getenv('PROCESSED_FOLDER', 'processed'),
            'error': os.getenv('ERROR_FOLDER', 'error'),
            'archive': os.getenv('ARCHIVE_FOLDER', 'archive'),
            'logs': os.getenv('LOGS_FOLDER', 'logs')
        }

        # Create root watch folder if it doesn't exist
        root_path = Path(watch_folder)
        if not root_path.exists():
            root_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created root watch folder: {watch_folder}")

        # Create all subfolders
        for folder_name, folder_path in subfolders.items():
            full_path = root_path / folder_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created folder: {full_path}")

        logger.info("All required folders have been created successfully")
        return True

    except Exception as e:
        logger.error(f"Error creating folders: {str(e)}")
        logger.exception("Full traceback:")
        return False

def get_folder_path(folder_type):
    """
    Returns the full path for a specific folder type.
    Combines WATCH_FOLDER with the specific subfolder path.
    
    Args:
        folder_type (str): Type of folder ('inventory', 'orders', 'export', etc.)
    
    Returns:
        str: Full path to the folder
    """
    watch_folder = os.getenv('WATCH_FOLDER')
    if not watch_folder:
        logger.error("WATCH_FOLDER environment variable is not set")
        return None

    folder_mapping = {
        'inventory': os.getenv('INVENTORY_IMPORT_FOLDER', 'inventory'),
        'orders': os.getenv('ORDERS_IMPORT_FOLDER', 'orders'),
        'export': os.getenv('ORDERS_EXPORT_FOLDER', 'export'),
        'processed': os.getenv('PROCESSED_FOLDER', 'processed'),
        'error': os.getenv('ERROR_FOLDER', 'error'),
        'archive': os.getenv('ARCHIVE_FOLDER', 'archive'),
        'logs': os.getenv('LOGS_FOLDER', 'logs')
    }

    if folder_type not in folder_mapping:
        logger.error(f"Unknown folder type: {folder_type}")
        return None

    # Combine WATCH_FOLDER with the specific subfolder path
    return os.path.join(watch_folder, folder_mapping[folder_type]) 