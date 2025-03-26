import os
import pandas as pd
from celery import shared_task
from django.conf import settings
from ..models import MasterInventory
import logging
from datetime import datetime

# Set up logger
logger = logging.getLogger('inventory_import')

@shared_task(name='Portal.tasks.import_inventory.process_inventory_files')
def process_inventory_files():
    """Process inventory files from the specified folder"""
    try:
        logger.info("="*80)
        logger.info("Starting inventory file processing task")
        
        # Use the Inventory subfolder
        import_folder = os.path.join(settings.WATCH_FOLDER, 'Inventory')
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
            logger.info("No inventory files to process")
            return "No files to process"

        processed_count = 0
        error_count = 0
        
        for file in files:
            file_path = os.path.join(import_folder, file)
            logger.info(f"Processing inventory file: {file}")
            logger.info(f"Full file path: {file_path}")
            
            try:
                # Read Excel file
                df = pd.read_excel(file_path)
                logger.info(f"Successfully read Excel file. Found {len(df)} records in file {file}")
                logger.info(f"DataFrame columns: {list(df.columns)}")
                
                # Convert column names to lowercase for case-insensitive matching
                df.columns = df.columns.str.lower()
                
                # Process each row
                for _, row in df.iterrows():
                    try:
                        # Create or update inventory item
                        inventory_item, created = MasterInventory.objects.update_or_create(
                            item=row['item'],
                            defaults={
                                'description': row['description'],
                                'uom': row['uom'],
                                'cus1': row.get('cus1'),
                                'cus2': row.get('cus2'),
                                'cus3': row.get('cus3'),
                                'status': 0  # Reset status for new/updated items
                            }
                        )
                        
                        action = "Created" if created else "Updated"
                        logger.info(f"{action} inventory item: {row['item']}")
                        processed_count += 1
                        
                    except Exception as row_error:
                        logger.error(f"Error processing row {_} in file {file}: {str(row_error)}")
                        logger.error(f"Row data: {row.to_dict()}")
                        error_count += 1
                
                # Move file to processed folder
                processed_folder = os.path.join(settings.COMPLETED_FOLDER, 'Inventory')
                os.makedirs(processed_folder, exist_ok=True)
                processed_path = os.path.join(processed_folder, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                logger.info(f"Moving file from {file_path} to {processed_path}")
                os.rename(file_path, processed_path)
                logger.info(f"Successfully moved processed file to: {processed_path}")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file}: {str(file_error)}")
                logger.exception("Full traceback:")
                # Move file to error folder
                error_folder = os.path.join(settings.ERROR_FOLDER, 'Inventory')
                os.makedirs(error_folder, exist_ok=True)
                error_path = os.path.join(error_folder, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file}")
                os.rename(file_path, error_path)
                logger.error(f"Moved error file to: {error_path}")
                error_count += 1

        logger.info(f"Task completed. Processed {processed_count} items with {error_count} errors")
        return f"Processed {processed_count} items with {error_count} errors"
        
    except Exception as e:
        logger.error(f"Critical error in process_inventory_files: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 