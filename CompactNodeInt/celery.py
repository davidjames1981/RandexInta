import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CompactNodeInt.settings')

# Create the Celery app
app = Celery('CompactNodeInt')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Get task frequencies from environment variables (with fallback values)
import_frequency = float(os.getenv('IMPORT_FREQUENCY', 60))  # default 60 seconds
api_frequency = float(os.getenv('API_FREQUENCY', 10))  # default 10 seconds

# Configure the periodic tasks
app.conf.beat_schedule = {
    'check-excel-files': {
        'task': 'Portal.tasks.process_excel_files',
        'schedule': import_frequency,
    },
    'process-api-orders': {
        'task': 'Portal.tasks.api_order_creation.create_api_orders',
        'schedule': api_frequency,
    },
    'check-pick-status': {
        'task': 'Portal.tasks.check_pick_status',
        'schedule': api_frequency,  # Use same frequency as API orders
    },
}

# Configure Celery to use Redis as the broker and result backend
app.conf.broker_url = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0'
app.conf.result_backend = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0'

# Optional: Configure broker connection retry settings
app.conf.broker_connection_retry_on_startup = True

# Auto-discover tasks in all registered Django app configs
app.autodiscover_tasks(['Portal'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 