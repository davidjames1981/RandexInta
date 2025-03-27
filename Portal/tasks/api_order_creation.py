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
    Order type is determined by transaction_type:
    - PUT orders: order_type = 3
    - PICK orders: order_type = 4
    """
    logger.info("="*80)
    logger.info("Starting API order creation task")
    
    try:
        # Get configuration
        api_host = os.getenv('API_HOST')
        warehouse = os.getenv('WAREHOUSE')
        logger.debug(f"Configuration - API Host: {api_host}, Warehouse: {warehouse}")
        
        # Get all pending orders grouped by order number
        pending_orders = OrderData.objects.filter(sent_status=0).values('order_number', 'transaction_type').distinct()
        
        if pending_orders:
            logger.info(f"Found {len(pending_orders)} pending orders to process")
            logger.debug(f"Pending order numbers: {[order['order_number'] for order in pending_orders]}")
        else:
            logger.info("No pending orders found")
            return "No orders to process"
        
        api_url = f"{api_host}/api/full-order/"
        logger.info(f"API Endpoint: {api_url}")
        
        for order_group in pending_orders:
            order_number = order_group['order_number']
            transaction_type = order_group['transaction_type']
            
            # Set order_type based on transaction_type
            order_type = 4 if transaction_type == 'PICK' else 3  # 4 for PICK, 3 for PUT
            
            order_lines = OrderData.objects.filter(
                order_number=order_number,
                sent_status=0
            ).order_by('id')
            
            # Skip if no lines found
            if not order_lines:
                logger.warning(f"No lines found for order {order_number} despite being in pending orders")
                continue
                
            logger.info(f"\nProcessing {transaction_type} order {order_number} with {len(order_lines)} lines")
            logger.debug(f"Order lines for {order_number}: {list(order_lines.values())}")
            
            # Prepare API payload
            payload = {
                "name": order_number,
                "warehouse": warehouse,
                "order_type": order_type,  # Dynamic based on transaction_type
                "order_lines": []
            }
            
            # Add order lines with calculated line numbers
            for index, line in enumerate(order_lines, start=1):
                order_line = {
                    "line_number": index,
                    "item": line.item,
                    "quantity": line.quantity,
                    "suggested_bin": line.bin_location if line.bin_location else ""  # Empty string if bin_location is NULL
                }
                payload["order_lines"].append(order_line)
                logger.debug(f"Added line {index} to payload: {order_line}")
            
            # Log the full payload
            logger.info(f"Request Payload for {transaction_type} order {order_number}:")
            logger.debug(json.dumps(payload, indent=2))
                
            try:
                # Make API request with timeout
                logger.info(f"Sending request to API for {transaction_type} order {order_number}")
                logger.debug(f"Request URL: {api_url}")
                logger.debug(f"Request Headers: {{'Content-Type': 'application/json'}}")
                
                response = requests.post(
                    api_url, 
                    json=payload, 
                    timeout=30,  # 30 seconds timeout
                    headers={'Content-Type': 'application/json'}
                )
                
                # Log response details
                logger.info(f"Response Status Code: {response.status_code}")
                logger.debug(f"Response Headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    logger.debug(f"Response Body: {json.dumps(response_json, indent=2)}")
                except json.JSONDecodeError:
                    logger.warning(f"Response not JSON. Text: {response.text[:500]}")
                
                response.raise_for_status()
                
                # Update status to success
                order_lines.update(sent_status=1)
                logger.info(f"Successfully processed {transaction_type} order {order_number}")
                logger.debug(f"Updated {len(order_lines)} lines to sent_status=1")
                
            except requests.exceptions.Timeout:
                error_message = f"Timeout while connecting to API for {transaction_type} order {order_number}"
                logger.error(error_message)
                logger.debug(f"Request timed out after 30 seconds")
                order_lines.update(sent_status=99, api_error=error_message)
                
            except requests.exceptions.ConnectionError as e:
                error_message = f"Connection error for {transaction_type} order {order_number}: {str(e)}"
                logger.error(error_message)
                logger.debug(f"Connection Details: Host={api_host}")
                logger.exception("Full connection error traceback:")
                order_lines.update(sent_status=99, api_error=error_message)
                
            except requests.exceptions.RequestException as e:
                error_message = f"API error for {transaction_type} order {order_number}: {str(e)}"
                logger.error(error_message)
                logger.exception("Full API error traceback:")
                order_lines.update(sent_status=99, api_error=error_message)
                
    except Exception as e:
        logger.error(f"Critical error in create_api_orders task: {str(e)}")
        logger.exception("Full traceback:")
            
    logger.info("="*80)
    return "Order processing completed" 