# This file makes the tasks directory a Python package
import os
import django
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CompactNodeInt.settings')

# Initialize Django
django.setup()

# Import tasks after Django is initialized
from .import_order import process_excel_files
from .api_order_creation import create_api_orders
from .check_pick_status import check_pick_status
from .import_inventory import process_inventory_files
from .api_inventory import api_inventory_creation
from .export_order import export_completed_orders
from .import_db_orders import process_staging_orders
from .vlm_demo import process_demo_orders

# Register all tasks
__all__ = [
    'process_excel_files',
    'create_api_orders',
    'check_pick_status',
    'process_inventory_files',
    'api_inventory_creation',
    'export_completed_orders',
    'process_staging_orders',
    'process_demo_orders',
]

# Ensure tasks are registered with Celery
tasks = [
    process_excel_files,
    create_api_orders,
    check_pick_status,
    process_inventory_files,
    api_inventory_creation,
    export_completed_orders,
    process_staging_orders,
    process_demo_orders,
] 