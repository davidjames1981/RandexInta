import os
import requests
from celery import shared_task
from django.conf import settings
from Portal.models import MasterInventory
import logging
from datetime import datetime

# Set up logger
logger = logging.getLogger('inventory_api')

@shared_task(name='Portal.tasks.api_inventory.api_inventory_creation')
def api_inventory_creation():
    """
    Task to push new/pending inventory items to the external API system.
    Only processes items with status = 0 (pending).
    Updates status to 1 (processed) after successful API push.
    """
    try:
        # Get API configuration from settings
        api_host = settings.API_HOST
        if not api_host:
            logger.error("API_HOST not configured in settings")
            return "API_HOST not configured"

        # Get pending inventory items
        pending_items = MasterInventory.objects.filter(status=0)
        if not pending_items.exists():
            logger.info("No pending inventory items to process")
            return "No items to process"

        success_count = 0
        error_count = 0
        
        for item in pending_items:
            try:
                # Prepare API payload according to required format
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
                
                logger.info(f"Processing inventory item: {item.item}")
                logger.debug(f"API payload: {payload}")
                
                # Make API request
                response = requests.post(
                    f"{api_host}/api/item/",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 201:
                    # Update status to success
                    item.status = 1
                    item.save()
                    success_count += 1
                    logger.info(f"Successfully created inventory item: {item.item}")
                else:
                    # Update status to error
                    item.status = 2
                    item.save()
                    error_count += 1
                    logger.error(f"API error for item {item.item}: {response.text}")
                    
            except requests.exceptions.RequestException as req_error:
                # Handle request errors
                item.status = 2
                item.save()
                error_count += 1
                logger.error(f"Request error for item {item.item}: {str(req_error)}")
                
            except Exception as item_error:
                # Handle other errors
                item.status = 2
                item.save()
                error_count += 1
                logger.error(f"Error processing item {item.item}: {str(item_error)}")

        return f"Processed {success_count + error_count} items: {success_count} successful, {error_count} failed"
        
    except Exception as e:
        logger.error(f"Critical error in api_inventory_creation: {str(e)}")
        return f"Error: {str(e)}"

    return {
        'total': total_items,
        'success': success_count,
        'errors': error_count
    } 