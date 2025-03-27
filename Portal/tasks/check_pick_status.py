import os
import requests
from celery import shared_task
from Portal.models import OrderData
from dotenv import load_dotenv
from Portal.utils.logger import general_logger as logger
from collections import defaultdict

load_dotenv()

@shared_task(name='Portal.tasks.check_pick_status')
def check_pick_status():
    """
    Task to check pick status from API for orders that have been sent (status=1)
    Updates actual_qty and status=3 when pick data is found
    Handles both PUT (order_type=3) and PICK (order_type=4) orders
    """
    logger.info("="*80)
    logger.info("Starting pick status check task")
    
    try:
        # Get all orders with sent_status=1 or 99 (sent but not yet picked)
        sent_orders = OrderData.objects.filter(sent_status__in=[1, 99]).values('order_number', 'transaction_type').distinct()
        
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
                
                # Use defaultdict to sum up confirmed quantities for each item
                item_quantities = defaultdict(float)
                
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
                    
                    if item_name:
                        item_quantities[item_name] += quantity_confirmed
                        logger.info(f"Added {quantity_confirmed} to total for {item_name} ({transaction_type})")
                
                # Update each item with its total confirmed quantity
                for item_name, total_confirmed in item_quantities.items():
                    logger.info(f"Processing {transaction_type} order {order_number}, {item_name} with total confirmed quantity: {total_confirmed}")
                    
                    # Get the order line to check requested quantity
                    order_line = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).first()
                    
                    if not order_line:
                        logger.warning(f"No matching order found for {transaction_type} order {order_number}, item {item_name}")
                        continue
                    
                    # Update status based on quantity comparison    
                    update_data = {'actual_qty': total_confirmed}
                    if total_confirmed >= order_line.quantity:
                        update_data['sent_status'] = 3
                        logger.info(f"Order {order_number}, item {item_name} completed: requested={order_line.quantity}, confirmed={total_confirmed}")
                    else:
                        update_data['sent_status'] = 99
                        logger.info(f"Order {order_number}, item {item_name} still processing: requested={order_line.quantity}, confirmed={total_confirmed}")
                    
                    # Update the order line
                    updated = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        transaction_type=transaction_type,
                        sent_status__in=[1, 99]
                    ).update(**update_data)
                    
                    if updated:
                        logger.info(f"Updated {transaction_type} order {order_number}, item {item_name}: "
                                  f"actual_qty={total_confirmed}, status={update_data.get('sent_status', 1)}")
                    else:
                        logger.warning(f"Failed to update {transaction_type} order {order_number}, item {item_name}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API error checking status for {transaction_type} order {order_number}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_pick_status task: {str(e)}", exc_info=True)
        
    logger.info("="*80)
    return "Status check completed" 