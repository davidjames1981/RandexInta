import os
import json
from celery import shared_task
import requests
from django.db.models import Count
from Portal.models import OrderData
from dotenv import load_dotenv
from Portal.utils.logger import api_logger as logger

load_dotenv()

@shared_task(name='Portal.tasks.api_order_creation.create_api_orders')
def create_api_orders():
    """
    Task to create orders via API for records with sent_status = 0
    Updates sent_status to 1 on success, 99 on failure
    """
    logger.info("="*80)
    logger.info("Starting API order creation task")
    try:
        # Get all pending orders grouped by order number
        pending_orders = OrderData.objects.filter(sent_status=0).values('order_number').distinct()
        
        if pending_orders:
            logger.info(f"Found {len(pending_orders)} pending orders to process")
        else:
            logger.info("No pending orders found")
            return "No orders to process"
        
        api_url = f"{os.getenv('API_HOST')}/api/full-order/"
        logger.info(f"API Endpoint: {api_url}")
        logger.info(f"Warehouse: {os.getenv('WAREHOUSE')}")
        
        for order_group in pending_orders:
            order_number = order_group['order_number']
            order_lines = OrderData.objects.filter(
                order_number=order_number,
                sent_status=0
            ).order_by('id')
            
            # Skip if no lines found
            if not order_lines:
                logger.warning(f"No lines found for order {order_number}")
                continue
                
            logger.info(f"\nProcessing order {order_number} with {len(order_lines)} lines")
            
            # Prepare API payload
            payload = {
                "name": order_number,
                "warehouse": os.getenv('WAREHOUSE'),
                "order_type": 3,  # Hardcoded as per example
                "order_lines": []
            }
            
            # Add order lines with calculated line numbers
            for index, line in enumerate(order_lines, start=1):
                order_line = {
                    "line_number": index,
                    "item": line.item,
                    "quantity": line.quantity
                }
                payload["order_lines"].append(order_line)
            
            # Log the full payload
            logger.info(f"Request Payload for order {order_number}:")
            logger.info(json.dumps(payload, indent=2))
                
            try:
                # Make API request with timeout
                logger.info(f"Sending request to API for order {order_number}")
                response = requests.post(
                    api_url, 
                    json=payload, 
                    timeout=30,  # 30 seconds timeout
                    headers={'Content-Type': 'application/json'}
                )
                
                # Log response details
                logger.info(f"Response Status Code: {response.status_code}")
                logger.info(f"Response Headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    logger.info(f"Response Body: {json.dumps(response_json, indent=2)}")
                except json.JSONDecodeError:
                    logger.info(f"Response Text: {response.text}")
                
                response.raise_for_status()
                
                # Update status to success
                order_lines.update(sent_status=1)
                logger.info(f"Successfully processed order {order_number}")
                
            except requests.exceptions.Timeout:
                error_message = f"Timeout while connecting to API for order {order_number}"
                logger.error(error_message)
                order_lines.update(sent_status=99, api_error=error_message)
                
            except requests.exceptions.ConnectionError as e:
                error_message = f"Connection error for order {order_number}: {str(e)}"
                logger.error(error_message)
                logger.error(f"Connection Details: Host={os.getenv('API_HOST')}, Port=8000")
                order_lines.update(sent_status=99, api_error=error_message)
                
            except requests.exceptions.RequestException as e:
                error_message = f"API error for order {order_number}: {str(e)}"
                logger.error(error_message)
                order_lines.update(sent_status=99, api_error=error_message)
                
    except Exception as e:
        logger.error(f"Critical error in create_api_orders task: {str(e)}")
        logger.exception("Full traceback:")
            
    logger.info("="*80)
    return "Order processing completed" 