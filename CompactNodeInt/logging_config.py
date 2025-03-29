import os
from pathlib import Path
from Portal.utils.path_utils import get_watch_path

def get_logging_config():
    """
    Returns the logging configuration using the watch folder structure
    """
    # Get the logs directory path
    logs_dir = get_watch_path(os.getenv('LOGS_FOLDER'))
    
    # Create task-specific log files
    log_files = {
        'general': os.path.join(logs_dir, 'general.log'),
        'celery': os.path.join(logs_dir, 'celery.log'),
        'django': os.path.join(logs_dir, 'django.log'),
        
        # Task-specific logs
        'db_order_import': os.path.join(logs_dir, 'tasks', 'db_order_import.log'),
        'excel_order_import': os.path.join(logs_dir, 'tasks', 'excel_order_import.log'),
        'excel_order_export': os.path.join(logs_dir, 'tasks', 'excel_order_export.log'),
        'inventory_import': os.path.join(logs_dir, 'tasks', 'inventory_import.log'),
        'api_create_inventory': os.path.join(logs_dir, 'tasks', 'api_create_inventory.log'),
        'api_create_orders': os.path.join(logs_dir, 'tasks', 'api_create_orders.log'),
        'api_check_status': os.path.join(logs_dir, 'tasks', 'api_check_status.log'),
        
        # API and error logs
        'api': os.path.join(logs_dir, 'api.log'),
        'errors': os.path.join(logs_dir, 'errors.log'),
    }
    
    # Ensure tasks directory exists
    os.makedirs(os.path.join(logs_dir, 'tasks'), exist_ok=True)

    # Common formatter for all logs
    formatters = {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    }

    # Create handlers for each log file
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
    }

    # Add file handlers for each log file
    for name, path in log_files.items():
        handlers[f'{name}_file'] = {
            'class': 'logging.FileHandler',
            'filename': path,
            'formatter': 'verbose',
            'level': 'INFO',
        }

    # Configure loggers
    loggers = {
        # Django and Celery loggers
        'django': {
            'handlers': ['console', 'django_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Task loggers
        'db_order_import': {
            'handlers': ['console', 'db_order_import_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'excel_order_import': {
            'handlers': ['console', 'excel_order_import_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'excel_order_export': {
            'handlers': ['console', 'excel_order_export_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'inventory_import': {
            'handlers': ['console', 'inventory_import_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_create_inventory': {
            'handlers': ['console', 'api_create_inventory_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_create_orders': {
            'handlers': ['console', 'api_create_orders_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_check_status': {
            'handlers': ['console', 'api_check_status_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # General API logger
        'api': {
            'handlers': ['console', 'api_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Root logger for uncaught logs
        '': {
            'handlers': ['console', 'general_file', 'errors_file'],
            'level': 'INFO',
        },
    }

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers,
    } 