import os
import time
import json
import requests
from celery import shared_task
from dotenv import load_dotenv
from Portal.utils.logger import vlm_demo_logger as logger
from django.conf import settings
from datetime import datetime
from Portal.models import TaskConfig, TransactionLog

load_dotenv()

@shared_task(name='Portal.tasks.vlm_demo.process_demo_orders')
def process_demo_orders():
    """
    Task to process orders in demo mode for VLM exhibition.
    This task will:
    1. Get orders from the API
    2. Allocate non-manual orders
    3. Start non-manual orders
    4. Monitor processor status
    5. Complete tasks after 15 seconds
    """
    # Check if task is enabled in TaskConfig
    try:
        task_config = TaskConfig.objects.get(task_name='Portal.tasks.vlm_demo.process_demo_orders')
        if not task_config.is_enabled:
            logger.info("VLM demo task is disabled in TaskConfig")
            return "Task disabled"
    except TaskConfig.DoesNotExist:
        logger.error("VLM demo task not found in TaskConfig")
        return "Task not configured"
    
    logger.info("="*80)
    logger.info("Starting VLM demo mode task")
    
    try:
        # Get API configuration
        api_host = os.getenv('API_HOST', 'http://18.135.240.39:8000')
        processor_id = os.getenv('PROCESSOR_ID', 'RX01')
        
        logger.info(f"Configuration - API Host: {api_host}, Processor ID: {processor_id}")
        
        while True:
            try:
                # Step 1: Get orders
                orders_url = f"{api_host}/api/order/?limit=25&offset=0&search=&order_type__in=3,4,6,7,8,9&allocation_status=&status="
                logger.info(f"Fetching orders from: {orders_url}")
                
                response = requests.get(orders_url, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                
                logger.debug(f"Orders API Response: {json.dumps(response_data, indent=2)}")
                
                # Extract orders from the results key
                orders = response_data.get('results', [])
                
                if not orders:
                    logger.info("No orders found, waiting 10 seconds before next check")
                    time.sleep(10)
                    continue
                
                logger.info(f"Found {len(orders)} orders to process")
                
                # Step 2: Process each non-manual order
                for order in orders:
                    order_id = order['id']
                    order_name = order['name']
                    
                    logger.info(f"Processing order: {order_name} (ID: {order_id})")
                    logger.debug(f"Order details: {json.dumps(order, indent=2)}")
                    
                    # Skip manual orders
                    if 'Manual' in order_name:
                        logger.info(f"Skipping manual order: {order_name}")
                        continue
                    
                    # Log order fetch
                    TransactionLog.objects.create(
                        order_id=order_id,
                        order_name=order_name,
                        action='fetch_order',
                        status='success',
                        details=order  # Don't pre-serialize the JSON
                    )
                    
                    # Allocate order
                    allocate_url = f"{api_host}/api/order/{order_id}/allocate"
                    logger.info(f"Allocating order: {allocate_url}")
                    
                    response = requests.post(allocate_url, timeout=30)
                    response.raise_for_status()
                    allocation_result = response.json()
                    
                    logger.info(f"Allocation result: {json.dumps(allocation_result, indent=2)}")
                    
                    # Log allocation
                    TransactionLog.objects.create(
                        order_id=order_id,
                        order_name=order_name,
                        action='allocate_order',
                        status='success',
                        details=allocation_result  # Don't pre-serialize the JSON
                    )
                    
                    # Start order
                    start_url = f"{api_host}/api/order/{order_id}/start"
                    logger.info(f"Starting order: {start_url}")
                    
                    response = requests.post(start_url, timeout=30)
                    response.raise_for_status()
                    start_result = response.json()
                    
                    logger.info(f"Start result: {json.dumps(start_result, indent=2)}")
                    
                    # Log start
                    TransactionLog.objects.create(
                        order_id=order_id,
                        order_name=order_name,
                        action='start_order',
                        status='success',
                        details=start_result  # Don't pre-serialize the JSON
                    )
                    
                    # Step 3: Monitor processor status
                    while True:
                        processor_url = f"{api_host}/api/processor/{processor_id}"
                        logger.info(f"Checking processor status: {processor_url}")
                        
                        response = requests.get(processor_url, timeout=30)
                        response.raise_for_status()
                        processor_tasks = response.json()
                        
                        logger.debug(f"Processor status response: {json.dumps(processor_tasks, indent=2)}")
                        
                        if not processor_tasks:
                            logger.info("No tasks currently processing")
                            break
                        
                        # Process each task
                        for task in processor_tasks:
                            task_id = task['task_id']
                            task_quantity = task['task_quantity']
                            
                            logger.info(f"Found task {task_id} with quantity {task_quantity}")
                            logger.debug(f"Task details: {json.dumps(task, indent=2)}")
                            
                            # Wait 15 seconds before completing
                            logger.info("Waiting 15 seconds before completing task")
                            time.sleep(15)
                            
                            # Complete task
                            complete_url = f"{api_host}/api/confirm-from-displaytool"
                            payload = {
                                "task_id": task_id,
                                "quantity_measured": None,
                                "quantity_input": task_quantity,
                                "isContainerFullQ": False
                            }
                            
                            logger.info(f"Completing task: {complete_url}")
                            logger.debug(f"Completion payload: {json.dumps(payload, indent=2)}")
                            
                            response = requests.post(complete_url, json=payload, timeout=30)
                            response.raise_for_status()
                            
                            logger.info("Task completed successfully")
                    
                    logger.info(f"Finished processing order: {order_name}")
                
                # Wait 10 seconds before checking for new orders
                logger.info("Waiting 10 seconds before checking for new orders")
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API error: {str(e)}")
                logger.exception("Full traceback:")
                time.sleep(10)  # Wait before retrying
                continue
                
    except Exception as e:
        logger.error(f"Critical error in process_demo_orders task: {str(e)}")
        logger.exception("Full traceback:")
        
    logger.info("="*80)
    return "Demo mode processing completed"

@shared_task
def vlm_demo_task():
    logger = TaskConfig.get_logger('vlm_demo')
    
    while True:
        try:
            # Fetch orders from API
            response = requests.get(settings.VLM_API_ENDPOINT)
            response.raise_for_status()
            orders = response.json()
            
            # Filter out orders with "Manual" in name
            filtered_orders = [order for order in orders if "Manual" not in order.get('name', '')]
            
            for order in filtered_orders:
                try:
                    # Log order fetch
                    TransactionLog.objects.create(
                        order_id=order.get('id'),
                        order_name=order.get('name'),
                        action='fetch_order',
                        status='success',
                        details=order  # Don't pre-serialize the JSON
                    )
                    
                    # Allocate order
                    allocate_response = requests.post(
                        f"{settings.VLM_API_ENDPOINT}/allocate",
                        json={'order_id': order['id']}
                    )
                    allocate_response.raise_for_status()
                    
                    # Log allocation
                    TransactionLog.objects.create(
                        order_id=order.get('id'),
                        order_name=order.get('name'),
                        action='allocate_order',
                        status='success',
                        details=allocate_response.json()  # Don't pre-serialize the JSON
                    )
                    
                    # Start order
                    start_response = requests.post(
                        f"{settings.VLM_API_ENDPOINT}/start",
                        json={'order_id': order['id']}
                    )
                    start_response.raise_for_status()
                    
                    # Log start
                    TransactionLog.objects.create(
                        order_id=order.get('id'),
                        order_name=order.get('name'),
                        action='start_order',
                        status='success',
                        details=start_response.json()  # Don't pre-serialize the JSON
                    )
                    
                    # Check processing status
                    while True:
                        status_response = requests.get(
                            f"{settings.VLM_API_ENDPOINT}/status/{order['id']}"
                        )
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        
                        # Log status check
                        TransactionLog.objects.create(
                            order_id=order.get('id'),
                            order_name=order.get('name'),
                            action='check_status',
                            status='success',
                            details=json.dumps(status_data)
                        )
                        
                        if status_data.get('status') == 'completed':
                            break
                        time.sleep(5)
                    
                    # Confirm task
                    confirm_response = requests.post(
                        f"{settings.VLM_API_ENDPOINT}/confirm",
                        json={
                            'order_id': order['id'],
                            'processed_quantity': status_data.get('processed_quantity', 0)
                        }
                    )
                    confirm_response.raise_for_status()
                    
                    # Log confirmation
                    TransactionLog.objects.create(
                        order_id=order.get('id'),
                        order_name=order.get('name'),
                        action='confirm_task',
                        status='success',
                        details=json.dumps(confirm_response.json())
                    )
                    
                except Exception as e:
                    # Log error
                    TransactionLog.objects.create(
                        order_id=order.get('id'),
                        order_name=order.get('name'),
                        action='process_order',
                        status='error',
                        error_message=str(e)
                    )
                    logger.error(f"Error processing order {order.get('id')}: {str(e)}")
                    continue
            
            time.sleep(30)  # Wait before next iteration
            
        except Exception as e:
            logger.error(f"Error in VLM demo task: {str(e)}")
            time.sleep(30)  # Wait before retrying 