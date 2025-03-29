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
    Updates actual_qty, shortage_qty and status based on confirmed/shortage quantities
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
                
                # Dictionary to store quantities by item and line number
                line_data = defaultdict(lambda: {'confirmed': 0, 'shortage': 0, 'latest_shortage_id': 0})
                
                # Process each history record
                for record in history_data:
                    order_type = record.get('order_type')
                    history_type = record.get('history_type')
                    expected_order_type = 4 if transaction_type == 'PICK' else 3
                    
                    # Skip records that don't match our order type or aren't confirmed/shortage
                    if order_type != expected_order_type or history_type not in [1, 5]:
                        logger.debug(f"Skipping record with mismatched order_type: {order_type} (expected {expected_order_type}) or history_type: {history_type}")
                        continue
                        
                    item_name = record.get('item_name')
                    line_number = record.get('order_line_number')
                    record_id = record.get('id', 0)
                    
                    if item_name and line_number is not None:
                        line_key = (item_name, line_number)
                        if history_type == 1:
                            # For confirmed picks - sum up the quantities
                            quantity_confirmed = record.get('quantity_confirmed', 0)
                            line_data[line_key]['confirmed'] += quantity_confirmed
                            logger.info(f"Added confirmed quantity {quantity_confirmed} for {item_name} (Line {line_number}), total now: {line_data[line_key]['confirmed']}")
                        elif history_type == 5:
                            # For shortages - take the most recent one
                            if record_id > line_data[line_key]['latest_shortage_id']:
                                shortage_qty = record.get('quantity_requested', 0)
                                line_data[line_key]['shortage'] = shortage_qty
                                line_data[line_key]['latest_shortage_id'] = record_id
                                logger.info(f"Updated shortage quantity to {shortage_qty} for {item_name} (Line {line_number}) from record {record_id}")
                
                # Update each item line with its quantities
                for (item_name, line_number), quantities in line_data.items():
                    logger.info(f"Processing {transaction_type} order {order_number}, {item_name}, Line {line_number}")
                    logger.info(f"Final quantities - Total Confirmed: {quantities['confirmed']}, Latest Shortage: {quantities['shortage']}")
                    
                    # Get the specific order line
                    order_line = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        order_line=line_number,
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).first()
                    
                    if not order_line:
                        logger.warning(f"No matching order found for {transaction_type} order {order_number}, item {item_name}, Line {line_number}")
                        continue
                    
                    # Update data based on quantities
                    update_data = {
                        'actual_qty': quantities['confirmed'],
                        'shortage_qty': quantities['shortage']
                    }
                    
                    # Determine status based on confirmed and shortage quantities
                    if quantities['confirmed'] == order_line.quantity:
                        # Quantities match exactly
                        update_data['sent_status'] = 3
                        logger.info(f"Order completed - exact match: requested={order_line.quantity}, confirmed={quantities['confirmed']}")
                    elif quantities['shortage'] > 0:
                        # Have shortage record - mark as complete
                        update_data['sent_status'] = 3
                        logger.info(f"Order completed with shortage: confirmed={quantities['confirmed']}, shortage={quantities['shortage']}")
                    else:
                        # Still processing
                        update_data['sent_status'] = 99
                        logger.info(f"Order still processing: requested={order_line.quantity}, confirmed={quantities['confirmed']}")
                    
                    # Update the specific order line
                    updated = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        order_line=line_number,
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).update(**update_data)
                    
                    if updated:
                        logger.info(f"Updated {transaction_type} order {order_number}, Line {line_number}: "
                                  f"actual_qty={update_data['actual_qty']}, "
                                  f"shortage_qty={update_data['shortage_qty']}, "
                                  f"status={update_data['sent_status']}")
                    else:
                        logger.warning(f"Failed to update {transaction_type} order {order_number}, Line {line_number}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API error checking status for {transaction_type} order {order_number}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_pick_status task: {str(e)}", exc_info=True)
        
    logger.info("="*80)
    return "Status check completed" 