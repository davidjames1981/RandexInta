import os
import logging
from celery import shared_task
from django.utils import timezone
from ..models import OrderData, TaskConfig
import pandas as pd
import shutil
from ..utils.path_utils import get_watch_path

# Set up logger
logger = logging.getLogger('excel_order_import')

@shared_task(name='Portal.tasks.excel_order_import')
def process_excel_orders():
    """Process orders from Excel files in the watch folder"""
    try:
        logger.info("="*80)
        logger.info("Starting Excel order import task")

        # Get task configuration and update timestamps
        task_config = TaskConfig.objects.filter(task_name='Portal.tasks.excel_order_import').first()
        if task_config:
            task_config.last_run = timezone.now()
            task_config.next_run = task_config.last_run + timezone.timedelta(seconds=task_config.frequency)
            task_config.save()

        # Get folder paths
        watch_folder = get_watch_path(os.getenv('ORDERS_IMPORT_FOLDER'))
        processed_folder = get_watch_path(os.getenv('PROCESSED_FOLDER'))
        error_folder = get_watch_path(os.getenv('ERROR_FOLDER'))

        logger.info(f"Watching folder: {watch_folder}")
        logger.info(f"Processed folder: {processed_folder}")
        logger.info(f"Error folder: {error_folder}")

        # Rest of your existing code for processing Excel files
        # Just replace any direct folder path references with the variables above

    except Exception as e:
        logger.error(f"Critical error in process_excel_orders task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 