import os
import shutil
import pandas as pd
from celery import shared_task
from datetime import datetime
from Portal.models import MasterInventory
from django.conf import settings
from dotenv import load_dotenv
from Portal.utils.logger import import_logger as logger

# Load environment variables
load_dotenv()

# Get folder paths from environment variables
WATCH_FOLDER = os.path.join(os.getenv('WATCH_FOLDER'), 'Inventory')
COMPLETED_FOLDER = os.path.join(os.getenv('COMPLETED_FOLDER'), 'Inventory')
ERROR_FOLDER = os.path.join(os.getenv('ERROR_FOLDER'), 'Inventory')

# Required columns (case-insensitive)
REQUIRED_COLUMNS = ['item', 'description', 'uom']

def get_column_mapping(df):
    """
    Get mapping of required columns to actual column names in DataFrame
    Returns None if any required column is missing
    """
    logger.debug("Checking column mapping")
    df_columns = {col.lower().replace(' ', '_'): col for col in df.columns}
    mapping = {}
    
    for required_col in REQUIRED_COLUMNS:
        if required_col not in df_columns:
            logger.warning(f"Required column '{required_col}' not found in DataFrame columns: {list(df.columns)}")
            return None
        mapping[required_col] = df_columns[required_col]
    
    logger.debug(f"Column mapping successful: {mapping}")
    return mapping

@shared_task(name='Portal.tasks.import_inventory.process_inventory_files')
def process_inventory_files():
    """Process Excel files from the inventory watch folder"""
    logger.info("="*80)
    logger.info("Starting Inventory Excel file processing task")
    try:
        # Check if the folders exist
        for folder in [WATCH_FOLDER, COMPLETED_FOLDER, ERROR_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                logger.info(f"Created folder: {folder}")
            else:
                logger.debug(f"Folder exists: {folder}")

        # Look for Excel files in the watch folder
        logger.debug(f"Scanning watch folder: {WATCH_FOLDER}")
        excel_files = [f for f in os.listdir(WATCH_FOLDER) 
                      if f.endswith(('.xlsx', '.xls')) and 
                      os.path.isfile(os.path.join(WATCH_FOLDER, f))]
        
        if excel_files:
            logger.info(f"Found {len(excel_files)} Excel files to process: {excel_files}")
        else:
            logger.info("No Excel files found in watch folder")
            return "No files to process"
        
        for file_name in excel_files:
            file_path = os.path.join(WATCH_FOLDER, file_name)
            logger.info(f"\nProcessing file: {file_name}")
            logger.debug(f"Full file path: {file_path}")
            
            try:
                # Read the Excel file
                logger.debug(f"Reading Excel file: {file_name}")
                df = pd.read_excel(file_path)
                records_count = len(df)
                logger.info(f"Found {records_count} records in {file_name}")
                logger.debug(f"DataFrame columns: {list(df.columns)}")
                
                # Get column mapping
                column_mapping = get_column_mapping(df)
                if column_mapping is None:
                    error_msg = f"Missing required columns. Required: {REQUIRED_COLUMNS}, Found: {list(df.columns)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Column mapping found: {column_mapping}")
                
                # Process each row
                success_count = 0
                error_count = 0
                for index, row in df.iterrows():
                    try:
                        # Log row data for debugging
                        row_data = {
                            'item': row[column_mapping['item']],
                            'description': row[column_mapping['description']],
                            'uom': row[column_mapping['uom']],
                            'cus1': row.get(column_mapping.get('cus1', 'cus1'), None),
                            'cus2': row.get(column_mapping.get('cus2', 'cus2'), None),
                            'cus3': row.get(column_mapping.get('cus3', 'cus3'), None)
                        }
                        logger.debug(f"Processing row {index + 1}: {row_data}")
                        
                        # Update or create the inventory item
                        MasterInventory.objects.update_or_create(
                            item=row_data['item'],
                            defaults={
                                'description': row_data['description'],
                                'uom': row_data['uom'],
                                'cus1': row_data['cus1'],
                                'cus2': row_data['cus2'],
                                'cus3': row_data['cus3'],
                                'status': 0  # Reset status for new imports
                            }
                        )
                        success_count += 1
                        logger.debug(f"Successfully processed row {index + 1}")
                    except Exception as row_error:
                        error_count += 1
                        logger.error(f"Error processing row {index + 1} in {file_name}: {str(row_error)}")
                        logger.debug(f"Problematic row data: {row_data}")
                        raise row_error

                # Move file to completed folder with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{timestamp}_{file_name}"
                completed_path = os.path.join(COMPLETED_FOLDER, new_filename)
                logger.debug(f"Moving file to completed folder: {completed_path}")
                
                shutil.move(file_path, completed_path)
                logger.info(f"Successfully processed {success_count}/{records_count} records from {file_name}")
                if error_count > 0:
                    logger.warning(f"Encountered {error_count} errors while processing {file_name}")
                logger.info(f"Moved {file_name} to completed folder as {new_filename}")

            except Exception as e:
                # If there's an error, move file to error folder with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                error_filename = f"{timestamp}_{file_name}"
                error_path = os.path.join(ERROR_FOLDER, error_filename)
                logger.debug(f"Moving file to error folder: {error_path}")
                
                shutil.move(file_path, error_path)
                logger.error(f"Error processing {file_name}: {str(e)}")
                logger.exception("Full traceback:")
                logger.info(f"Moved {file_name} to error folder as {error_filename}")

    except Exception as e:
        logger.error(f"Critical error in process_inventory_files task: {str(e)}")
        logger.exception("Full traceback:")

    logger.info("="*80)
    return "Inventory Excel file processing completed" 