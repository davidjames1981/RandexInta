import os
import requests
from celery import shared_task
from Portal.models import OrderData
from dotenv import load_dotenv
from Portal.utils.logger import general_logger as logger
from collections import defaultdict
from datetime import datetime, timedelta

load_dotenv()

# Number of days to wait before marking status 99 records as complete
TIMEOUT_DAYS = 1  # Adjust this value as needed

@shared_task(name='Portal.tasks.check_pick_status')
def check_pick_status():
    """
    Task to check pick status from API for orders that have been sent (status=1)
    Updates actual_qty and status=3 when pick data is found
    Handles both PUT (order_type=3) and PICK (order_type=4) orders
    Also handles timeout for records stuck in status 99
    """
    logger.info("="*80)
    logger.info("Starting pick status check task")
    
    try:
        # Calculate the timeout date
        timeout_date = datetime.now() - timedelta(days=TIMEOUT_DAYS)
        
        # First, handle timeout for status 99 records
        timeout_orders = OrderData.objects.filter(
            sent_status=99,
            inserted_date__lt=timeout_date
        )
        
        if timeout_orders.exists():
            logger.info(f"Found {timeout_orders.count()} orders that have timed out after {TIMEOUT_DAYS} days")
            timeout_orders.update(sent_status=3)
            logger.info("Updated timed out orders to status 3")
        
        # Get all orders with sent_status=1 or 99 (sent but not yet picked)
        sent_orders = OrderData.objects.filter(
            sent_status__in=[1, 99],
            inserted_date__gte=timeout_date  # Only check orders within the timeout period
        ).values('order_number', 'transaction_type').distinct()
        
        if not sent_orders:
            logger.info("No sent orders found to check")
            return "No orders to check"
            
        api_host = os.getenv('API_HOST', '').rstrip('/')
        
        for order_group in sent_orders:
            order_number = order_group['order_number']
            transaction_type = order_group['transaction_type']
            logger.info(f"Checking status for {transaction_type} order: {order_number}")
            
            try:
                # Make API request
                api_url = f"{api_host}/api/history/?order_name={order_number}"
                logger.info(f"Making API request to: {api_url}")
                response = requests.get(api_url, timeout=30)
                response.raise_for_status()
                history_data = response.json()
                
                if not history_data:
                    logger.info(f"No history data found for order {order_number}")
                    continue
                
                logger.info(f"Received {len(history_data)} history records for order {order_number}")
                
                # Dictionary to store confirmed quantities by item and line number
                line_quantities = defaultdict(float)
                
                # Process each history record
                for record in history_data:
                    # Check if order_type matches transaction_type and history_type is 1
                    order_type = record.get('order_type')
                    history_type = record.get('history_type')
                    expected_order_type = 4 if transaction_type == 'PICK' else 3
                    
                    if order_type != expected_order_type or history_type != 1:
                        logger.debug(f"Skipping record with mismatched order_type: {order_type} (expected {expected_order_type}) or history_type: {history_type} (expected 1)")
                        continue
                        
                    item_name = record.get('item_name')
                    quantity_confirmed = record.get('quantity_confirmed', 0)
                    line_number = record.get('order_line_number')
                    
                    if item_name and line_number is not None:
                        # Create a unique key for each item+line combination
                        line_key = (item_name, line_number)
                        line_quantities[line_key] += quantity_confirmed
                        logger.info(f"Added {quantity_confirmed} to total for {item_name} (Line {line_number}, {transaction_type})")
                
                # Update each item line with its confirmed quantity
                for (item_name, line_number), total_confirmed in line_quantities.items():
                    logger.info(f"Processing {transaction_type} order {order_number}, {item_name}, Line {line_number} with total confirmed quantity: {total_confirmed}")
                    
                    # Get the specific order line
                    order_line = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        order_line=line_number,  # Match the specific line number
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).first()
                    
                    if not order_line:
                        logger.warning(f"No matching order found for {transaction_type} order {order_number}, item {item_name}, Line {line_number}")
                        continue
                    
                    # Update status based on quantity comparison    
                    update_data = {'actual_qty': total_confirmed}
                    if total_confirmed >= order_line.quantity:
                        update_data['sent_status'] = 3
                        logger.info(f"Order {order_number}, Line {line_number}, item {item_name} completed: requested={order_line.quantity}, confirmed={total_confirmed}")
                    else:
                        update_data['sent_status'] = 99
                        logger.info(f"Order {order_number}, Line {line_number}, item {item_name} still processing: requested={order_line.quantity}, confirmed={total_confirmed}")
                    
                    # Update the specific order line
                    updated = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        order_line=line_number,  # Match the specific line number
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).update(**update_data)
                    
                    if updated:
                        logger.info(f"Updated {transaction_type} order {order_number}, Line {line_number}, item {item_name}: "
                                  f"actual_qty={total_confirmed}, status={update_data.get('sent_status', 1)}")
                    else:
                        logger.warning(f"Failed to update {transaction_type} order {order_number}, Line {line_number}, item {item_name}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API error checking status for {transaction_type} order {order_number}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_pick_status task: {str(e)}", exc_info=True)
        
    logger.info("="*80)
    return "Status check completed" 