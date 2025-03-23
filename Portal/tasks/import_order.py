import os
import shutil
import pandas as pd
from celery import shared_task
from datetime import datetime
from Portal.models import OrderData
from django.conf import settings
from dotenv import load_dotenv
from Portal.utils.logger import import_logger as logger

# Load environment variables
load_dotenv()

# Get folder paths from environment variables
WATCH_FOLDER = os.getenv('WATCH_FOLDER')
COMPLETED_FOLDER = os.getenv('COMPLETED_FOLDER')
ERROR_FOLDER = os.getenv('ERROR_FOLDER')

# Required columns (case-insensitive)
REQUIRED_COLUMNS = ['order_number', 'transaction_type', 'item', 'quantity']

def get_column_mapping(df):
    """
    Get mapping of required columns to actual column names in DataFrame
    Returns None if any required column is missing
    """
    df_columns = {col.lower().replace(' ', '_'): col for col in df.columns}
    mapping = {}
    
    for required_col in REQUIRED_COLUMNS:
        if required_col not in df_columns:
            return None
        mapping[required_col] = df_columns[required_col]
    
    return mapping

@shared_task(name='Portal.tasks.process_excel_files')
def process_excel_files():
    """Process Excel files from the watch folder"""
    try:
        # Check if the folders exist
        for folder in [WATCH_FOLDER, COMPLETED_FOLDER, ERROR_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                logger.info(f"Created folder: {folder}")

        # Look for Excel files in the watch folder
        excel_files = [f for f in os.listdir(WATCH_FOLDER) 
                      if f.endswith(('.xlsx', '.xls')) and 
                      os.path.isfile(os.path.join(WATCH_FOLDER, f))]
        
        if excel_files:
            logger.info(f"Found {len(excel_files)} Excel files to process")
        
        for file_name in excel_files:
            file_path = os.path.join(WATCH_FOLDER, file_name)
            try:
                logger.info(f"Processing file: {file_name}")
                
                # Read the Excel file
                df = pd.read_excel(file_path)
                records_count = len(df)
                logger.info(f"Found {records_count} records in {file_name}")
                
                # Get column mapping
                column_mapping = get_column_mapping(df)
                if column_mapping is None:
                    error_msg = f"Missing required columns. Required: {REQUIRED_COLUMNS}, Found: {list(df.columns)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Column mapping found: {column_mapping}")
                
                # Process each row
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        OrderData.objects.create(
                            order_number=row[column_mapping['order_number']],
                            transaction_type=row[column_mapping['transaction_type']],
                            item=row[column_mapping['item']],
                            quantity=row[column_mapping['quantity']],
                            file_name=file_name
                        )
                        success_count += 1
                    except Exception as row_error:
                        logger.error(f"Error processing row in {file_name}: {str(row_error)}")
                        raise row_error

                # Move file to completed folder with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{timestamp}_{file_name}"
                shutil.move(
                    file_path,
                    os.path.join(COMPLETED_FOLDER, new_filename)
                )
                logger.info(f"Successfully processed {success_count}/{records_count} records from {file_name}")
                logger.info(f"Moved {file_name} to completed folder as {new_filename}")

            except Exception as e:
                # If there's an error, move file to error folder with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                error_filename = f"{timestamp}_{file_name}"
                shutil.move(
                    file_path,
                    os.path.join(ERROR_FOLDER, error_filename)
                )
                logger.error(f"Error processing {file_name}: {str(e)}")
                logger.error(f"Moved {file_name} to error folder as {error_filename}")

    except Exception as e:
        logger.error(f"Critical error in process_excel_files task: {str(e)}")

    return None

# Schedule the task to run every 10 seconds
@shared_task
def schedule_file_processing():
    process_excel_files.delay() 