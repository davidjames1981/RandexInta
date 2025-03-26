import os
import pandas as pd
from celery import shared_task
from django.conf import settings
from ..models import OrderData
import logging
from datetime import datetime



# Set up logger
logger = logging.getLogger('order_import')

@shared_task(name='Portal.tasks.import_order.process_excel_files')
def process_excel_files():
    """Process Excel files from the specified folder"""
    try:
        logger.info("="*80)
        logger.info("Starting order file processing task")
        
        import_folder = os.path.join(settings.WATCH_FOLDER, 'Orders')
        logger.info(f"Looking for files in: {import_folder}")
        
        if not os.path.exists(import_folder):
            logger.warning(f"Import folder does not exist: {import_folder}")
            return "Import folder does not exist"

        # Get list of Excel files
        all_files = os.listdir(import_folder)
        logger.info(f"All files in directory: {all_files}")
        
        files = [f for f in all_files if f.endswith(('.xlsx', '.xls'))]
        logger.info(f"Excel files found: {files}")
        
        if not files:
            logger.info("No order files to process")
            return "No files to process"

        processed_count = 0
        error_count = 0
        
        for file in files:
            file_path = os.path.join(import_folder, file)
            logger.info(f"Processing order file: {file}")
            logger.info(f"Full file path: {file_path}")
            
            try:
                # Read Excel file
                df = pd.read_excel(file_path)
                logger.info(f"Successfully read Excel file. Found {len(df)} records")
                logger.info(f"DataFrame columns: {list(df.columns)}")
                
                # Convert column names to lowercase for case-insensitive matching
                df.columns = df.columns.str.lower()
                
                # Process each row
                for index, row in df.iterrows():
                    try:
                        # Map Excel columns to model fields
                        order_data = {
                            'order_number': row['order'],  # 'order' in Excel -> 'order_number' in model
                            'transaction_type': row['type'],  # 'type' in Excel -> 'transaction_type' in model
                            'item': row['item'],  # 'item' in Excel -> 'item' in model
                            'quantity': row['quantity'],
                            'sent_status': 0,  # Initial status
                            'file_name': file  # Store the source file name
                        }
                        
                        # Create order
                        order = OrderData.objects.create(**order_data)
                        logger.info(f"Created order: {order.order_number} - {order.item} (Qty: {order.quantity})")
                        processed_count += 1
                        
                    except KeyError as key_error:
                        logger.error(f"Missing required column in row {index}: {str(key_error)}")
                        logger.error(f"Available columns: {list(df.columns)}")
                        logger.error(f"Row data: {row.to_dict()}")
                        error_count += 1
                    except Exception as row_error:
                        logger.error(f"Error processing row {index} in file {file}: {str(row_error)}")
                        logger.error(f"Row data: {row.to_dict()}")
                        error_count += 1
                
                # Move file to processed folder
                processed_folder = os.path.join(settings.COMPLETED_FOLDER, 'Orders')
                os.makedirs(processed_folder, exist_ok=True)
                processed_path = os.path.join(processed_folder, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                logger.info(f"Moving file from {file_path} to {processed_path}")
                os.rename(file_path, processed_path)
                logger.info(f"Successfully moved processed file to: {processed_path}")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file}: {str(file_error)}")
                logger.exception("Full traceback:")
                # Move file to error folder
                error_folder = os.path.join(settings.ERROR_FOLDER, 'Orders')
                os.makedirs(error_folder, exist_ok=True)
                error_path = os.path.join(error_folder, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                os.rename(file_path, error_path)
                logger.error(f"Moved error file to: {error_path}")
                error_count += 1

        logger.info(f"Task completed. Processed {processed_count} orders with {error_count} errors")
        return f"Processed {processed_count} orders with {error_count} errors"
        
    except Exception as e:
        logger.error(f"Critical error in process_excel_files: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}"

# Schedule the task to run every 10 seconds
@shared_task
def schedule_file_processing():
    process_excel_files.delay() 