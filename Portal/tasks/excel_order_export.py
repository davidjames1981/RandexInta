import os
import logging
from celery import shared_task
from django.utils import timezone
from ..models import OrderData, TaskConfig
import pandas as pd
from ..utils.path_utils import get_watch_path

# Set up logger
logger = logging.getLogger('excel_order_export')

@shared_task(name='Portal.tasks.excel_order_export')
def export_orders():
    """Export orders to Excel files"""
    try:
        logger.info("="*80)
        logger.info("Starting Excel order export task")

        # Get task configuration and update timestamps
        task_config = TaskConfig.objects.filter(task_name='Portal.tasks.excel_order_export').first()
        if task_config:
            task_config.last_run = timezone.now()
            task_config.next_run = task_config.last_run + timezone.timedelta(seconds=task_config.frequency)
            task_config.save()

        # Get folder paths
        export_folder = get_watch_path(os.getenv('ORDERS_EXPORT_FOLDER'))
        archive_folder = get_watch_path(os.getenv('ARCHIVE_FOLDER'))

        logger.info(f"Export folder: {export_folder}")
        logger.info(f"Archive folder: {archive_folder}")

        # Rest of your existing code for exporting Excel files
        # Just replace any direct folder path references with the variables above

    except Exception as e:
        logger.error(f"Critical error in export_orders task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 