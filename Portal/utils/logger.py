import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .folder_setup import get_folder_path

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup a logger with file and console handlers"""
    # Get logs directory using folder_setup utility
    log_dir = get_folder_path('logs')
    if not log_dir:
        raise ValueError("Could not get logs folder path")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create formatter with more detailed information
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create and configure file handler with larger size and more backups
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Get or create logger
    logger = logging.getLogger(name)
    
    # Set logger level to the lowest level of handlers to catch all messages
    logger.setLevel(min(level, logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Ensure propagation is False to avoid duplicate logs
    logger.propagate = False

    return logger

# Create loggers for different components with DEBUG level for more detail
import_logger = setup_logger('import_task', 'import_task.log', level=logging.DEBUG)
api_logger = setup_logger('api_task', 'api_task.log', level=logging.DEBUG)
general_logger = setup_logger('general', 'general.log', level=logging.DEBUG) 