import os
import requests
from celery import shared_task
from django.conf import settings
from Portal.models import MasterInventory
from Portal.utils.logger import general_logger as logger

@shared_task(name='Portal.tasks.api_inventory.api_inventory_creation')
def api_inventory_creation():
    """
    Task to push new/pending inventory items to the external API system.
    Only processes items with status = 0 (pending).
    Updates status to 1 (processed) after successful API push.
    """
    try:
        # Get API configuration
        api_host = os.getenv('API_HOST', '').rstrip('/')
        api_endpoint = f"{api_host}/api/item/"
        
        logger.info("Starting inventory API creation task")
        
        # Get all pending inventory items
        pending_items = MasterInventory.objects.filter(status=0)
        total_items = pending_items.count()
        logger.info(f"Found {total_items} pending inventory items to process")
        
        if total_items == 0:
            logger.info("No pending inventory items to process")
            return
        
        success_count = 0
        error_count = 0
        
        for item in pending_items:
            try:
                # Prepare API payload
                payload = {
                    "name": item.item,
                    "info1": item.description,
                    "info2": item.cus1 or "",
                    "info3": item.cus2 or "",
                    "info4": item.cus3 or "",
                    "info5": "",
                    "image_link": "",
                    "item_code": "",
                    "item_category": "",
                    "unit": item.uom,
                    "unit_weight": 0,
                    "critical_stock_level": 0,
                    "quantity": 0
                }
                
                logger.debug(f"Sending inventory item {item.item} to API")
                logger.debug(f"API Payload: {payload}")
                
                # Make API request
                response = requests.post(
                    api_endpoint,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30  # 30 seconds timeout
                )
                
                # Check response
                response.raise_for_status()
                
                # Update item status on success
                item.status = 1  # Set to processed
                item.api_error = None  # Clear any previous errors
                item.save()
                
                success_count += 1
                logger.info(f"Successfully processed inventory item: {item.item}")
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_message = f"API request failed for item {item.item}: {str(e)}"
                logger.error(error_message)
                
                # Update item with error
                item.status = 2  # Set to error
                item.api_error = error_message
                item.save()
                
            except Exception as e:
                error_count += 1
                error_message = f"Unexpected error processing item {item.item}: {str(e)}"
                logger.error(error_message, exc_info=True)
                
                # Update item with error
                item.status = 2  # Set to error
                item.api_error = error_message
                item.save()
        
        # Log final statistics
        logger.info(f"Inventory API task completed. "
                   f"Processed: {total_items}, "
                   f"Success: {success_count}, "
                   f"Errors: {error_count}")
        
    except Exception as e:
        logger.error(f"Critical error in inventory API task: {str(e)}", exc_info=True)
        raise  # Re-raise to mark task as failed

    return {
        'total': total_items,
        'success': success_count,
        'errors': error_count
    } 