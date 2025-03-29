import os
import logging
import pandas as pd
from celery import shared_task
from django.utils import timezone
from ..models import MasterInventory
from ..utils.path_utils import get_watch_path

# Set up logger
logger = logging.getLogger('inventory_import')

@shared_task(name='Portal.tasks.import_inventory.process_inventory_files')
def process_inventory_files():
    """Process inventory files from the watch folder"""
    try:
        logger.info("="*80)
        logger.info("Starting inventory file processing task")

        # Get folder paths using the utility function
        watch_folder = get_watch_path(os.getenv('INVENTORY_IMPORT_FOLDER', 'inventory'))
        processed_folder = get_watch_path(os.getenv('PROCESSED_FOLDER', 'processed'))
        error_folder = get_watch_path(os.getenv('ERROR_FOLDER', 'error'))

        logger.info(f"Looking for files in: {watch_folder}")
        
        # Ensure all required folders exist
        os.makedirs(watch_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)
        os.makedirs(error_folder, exist_ok=True)

        # Get list of Excel files
        all_files = os.listdir(watch_folder)
        logger.info(f"All files in directory: {all_files}")
        
        files = [f for f in all_files if f.endswith(('.xlsx', '.xls'))]
        logger.info(f"Excel files found: {files}")
        
        if not files:
            logger.info("No inventory files to process")
            return "No files to process"

        processed_count = 0
        error_count = 0
        
        for file in files:
            file_path = os.path.join(watch_folder, file)
            logger.info(f"Processing inventory file: {file}")
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
                        inventory_data = {
                            # Required fields
                            'item': row['item'],
                            'description': row['description'],
                            'uom': row['uom'],
                            
                            # Optional fields
                            'cus1': row.get('cus1', None),
                            'cus2': row.get('cus2', None),
                            'cus3': row.get('cus3', None),
                            
                            # System fields
                            'status': 0  # Reset status for new/updated items
                        }
                        
                        # Create or update inventory record based on item (unique field)
                        inventory, created = MasterInventory.objects.update_or_create(
                            item=inventory_data['item'],
                            defaults=inventory_data
                        )
                        
                        action = "Created" if created else "Updated"
                        logger.info(f"{action} inventory record: {inventory.item} - {inventory.description}")
                        processed_count += 1
                        
                    except KeyError as key_error:
                        logger.error(f"Missing required column in row {index}: {str(key_error)}")
                        logger.error(f"Available columns: {list(df.columns)}")
                        logger.error(f"Row data: {row.to_dict()}")
                        error_count += 1
                    except Exception as row_error:
                        logger.error(f"Error processing row {index} in file {file}: {str(row_error)}")
                        logger.error(f"Row data: {row.to_dict()}")
                        logger.exception("Full traceback:")
                        error_count += 1
                
                # Move file to processed folder with timestamp
                processed_path = os.path.join(processed_folder, f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                logger.info(f"Moving file from {file_path} to {processed_path}")
                os.rename(file_path, processed_path)
                logger.info(f"Successfully moved processed file to: {processed_path}")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file}: {str(file_error)}")
                logger.exception("Full traceback:")
                # Move file to error folder with timestamp
                error_path = os.path.join(error_folder, f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                os.rename(file_path, error_path)
                logger.error(f"Moved error file to: {error_path}")
                error_count += 1

        logger.info(f"Task completed. Processed {processed_count} inventory records with {error_count} errors")
        return f"Processed {processed_count} inventory records with {error_count} errors"
        
    except Exception as e:
        logger.error(f"Critical error in process_inventory_files task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 