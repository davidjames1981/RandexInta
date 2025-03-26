import os
from celery import Celery
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment file not found at {env_path}")

load_dotenv(env_path, override=True)

# Print environment variables for debugging
print(f"REDIS_HOST from env (celery): {os.getenv('REDIS_HOST')}")
print(f"REDIS_PORT from env (celery): {os.getenv('REDIS_PORT')}")

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CompactNodeInt.settings')

# Create the Celery app
app = Celery('CompactNodeInt')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Get task frequencies from environment variables
import_frequency = float(os.getenv('IMPORT_FREQUENCY'))
if not import_frequency:
    raise ValueError("IMPORT_FREQUENCY environment variable is not set")

api_frequency = float(os.getenv('API_FREQUENCY'))
if not api_frequency:
    raise ValueError("API_FREQUENCY environment variable is not set")

pick_check_frequency = float(os.getenv('PICK_CHECK_FREQUENCY'))
if not pick_check_frequency:
    raise ValueError("PICK_CHECK_FREQUENCY environment variable is not set")

inventory_import_frequency = float(os.getenv('INVENTORY_IMPORT_FREQUENCY', '300'))  # Default 5 minutes

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'process_excel_files': {
        'task': 'Portal.tasks.process_excel_files',
        'schedule': int(os.getenv('IMPORT_FREQUENCY', 60)),
    },
    'create_api_orders': {
        'task': 'Portal.tasks.api_order_creation.create_api_orders',
        'schedule': int(os.getenv('API_FREQUENCY', 10)),
    },
    'check_pick_status': {
        'task': 'Portal.tasks.check_pick_status',
        'schedule': int(os.getenv('PICK_CHECK_FREQUENCY', 10)),
    },
    'import_inventory': {
        'task': 'Portal.tasks.import_inventory.process_inventory_files',
        'schedule': int(os.getenv('INVENTORY_IMPORT_FREQUENCY', 300)),
    },
    'api_inventory_creation': {
        'task': 'Portal.tasks.api_inventory.api_inventory_creation',
        'schedule': int(os.getenv('INVENTORY_API_FREQUENCY', 60)),  # Default to 1 minute
    },
}

# Configure Celery to use Redis as the broker and result backend
redis_host = os.getenv('REDIS_HOST')
if not redis_host:
    raise ValueError("REDIS_HOST environment variable is not set")

redis_port = os.getenv('REDIS_PORT')
if not redis_port:
    raise ValueError("REDIS_PORT environment variable is not set")

# Clean the values
redis_host = redis_host.strip().replace(' ', '')
redis_port = redis_port.strip()

# Ensure there are no spaces in the URLs
broker_url = f'redis://{redis_host}:{redis_port}/0'
result_backend = f'redis://{redis_host}:{redis_port}/0'

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

# Optional: Configure broker connection retry settings
app.conf.broker_connection_retry = True
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = 10

# Initialize Django
import django
django.setup()

# Import tasks after Django is initialized
from Portal.tasks import import_order, api_order_creation, check_pick_status, import_inventory

# Auto-discover tasks in all registered Django app configs
app.autodiscover_tasks(['Portal'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 