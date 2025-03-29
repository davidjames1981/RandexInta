from __future__ import absolute_import, unicode_literals
import os
from pathlib import Path
from celery import Celery
from django.conf import settings
from celery.signals import beat_init, worker_ready, task_prerun, task_postrun, task_failure
from django.utils import timezone
from datetime import timedelta
from celery.schedules import crontab
from dotenv import load_dotenv
import django

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment file not found at {env_path}")

load_dotenv(env_path, override=True)

# Print environment variables for debugging
print(f"REDIS_HOST from env: {os.getenv('REDIS_HOST')}")
print(f"REDIS_PORT from env: {os.getenv('REDIS_PORT')}")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CompactNodeInt.settings')

# Initialize Django
django.setup()

# Create the Celery app
app = Celery('CompactNodeInt')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure Celery to use Redis as the broker and result backend
redis_host = os.getenv('REDIS_HOST', 'localhost').strip().replace(' ', '')
redis_port = os.getenv('REDIS_PORT', '6379').strip()

broker_url = f'redis://{redis_host}:{redis_port}/0'
result_backend = f'redis://{redis_host}:{redis_port}/0'

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

# Optional: Configure broker connection retry settings
app.conf.broker_connection_retry = True
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = 10

# Enable task tracking
app.conf.task_track_started = True
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Configure beat scheduler
app.conf.beat_max_loop_interval = 1  # Check schedule every second
app.conf.beat_schedule_filename = 'celerybeat-schedule'

# Configure task defaults
app.conf.task_default_queue = 'celery'
app.conf.task_default_exchange = 'celery'
app.conf.task_default_routing_key = 'celery'
app.conf.task_default_delivery_mode = 'persistent'

def get_task_schedule():
    """
    Get task schedule from database configurations
    """
    try:
        from Portal.models import TaskConfig
        
        schedule = {}
        
        # Get enabled tasks from database
        enabled_tasks = TaskConfig.objects.filter(is_enabled=True)
        print(f"\nFound {enabled_tasks.count()} enabled tasks in database")
        
        for task in enabled_tasks:
            print(f"Processing task: {task.task_name} (Frequency: {task.frequency}s)")
            schedule[task.task_name] = {
                'task': task.task_name,
                'schedule': timedelta(seconds=float(task.frequency)),  # Convert to timedelta
                'options': {
                    'expires': float(task.frequency) - 1.0,
                    'queue': 'celery'
                }
            }
            print(f"Added task to schedule: {task.task_name}")

        print("\nFinal schedule:", schedule)
        return schedule
    except Exception as e:
        print(f"Error building schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

# Initialize beat schedule
app.conf.beat_schedule = get_task_schedule()

@app.task
def update_task_configs():
    """
    Update task configurations and their next run times
    """
    try:
        print("\nUpdating task configurations...")
        new_schedule = get_task_schedule()
        app.conf.beat_schedule = new_schedule
        
        # Update next run times in database
        from Portal.models import TaskConfig
        for task_config in TaskConfig.objects.filter(is_enabled=True):
            if task_config.last_run:
                task_config.next_run = task_config.last_run + timedelta(seconds=task_config.frequency)
                task_config.save()
                print(f"Updated next run time for {task_config.task_name}")
        
        return "Schedule updated successfully"
    except Exception as e:
        print(f"Error updating schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error updating schedule: {str(e)}"

@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **_):
    """Log when a task starts"""
    print(f"\nTask starting: {task.name}")
    print(f"Task ID: {task_id}")
    print(f"Arguments: {args}")
    print(f"Keyword arguments: {kwargs}")

@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, **_):
    """Log when a task completes"""
    print(f"\nTask completed: {task.name}")
    print(f"Task ID: {task_id}")
    print(f"Result: {retval}")

@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **_):
    """Log when a task fails"""
    print(f"\nTask failed: {task_id}")
    print(f"Exception: {exception}")
    print(f"Traceback: {einfo}")

@beat_init.connect
def init_beat(**kwargs):
    """
    Initialize beat schedule from database
    """
    print("\nInitializing beat schedule...")
    schedule = get_task_schedule()
    app.conf.beat_schedule = schedule
    print("Beat schedule initialized")

@worker_ready.connect
def at_worker_ready(**kwargs):
    """
    Signal handler called when worker is ready
    """
    print("\nWorker is ready!")
    print("Registered tasks:", app.tasks.keys())

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configure Celery logging
app.conf.update(
    worker_hijack_root_logger=False,  # Don't hijack root logger
    worker_redirect_stdouts=False,    # Don't redirect stdout/stderr
) 