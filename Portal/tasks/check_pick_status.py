import os
import requests
from celery import shared_task
from Portal.models import OrderData
from dotenv import load_dotenv
from Portal.utils.logger import general_logger as logger

load_dotenv()

@shared_task(name='Portal.tasks.check_pick_status')
def check_pick_status():
    """
    Task to check pick status from API for orders that have been sent (status=1)
    Updates actual_qty and status=3 when pick data is found
    """
    logger.info("="*80)
    logger.info("Starting pick status check task")
    
    try:
        # Get all orders with sent_status=1 (sent but not yet picked)
        sent_orders = OrderData.objects.filter(sent_status=1).values('order_number').distinct()
        
        if not sent_orders:
            logger.info("No sent orders found to check")
            return "No orders to check"
            
        api_host = os.getenv('API_HOST', '').rstrip('/')
        
        for order_group in sent_orders:
            order_number = order_group['order_number']
            logger.info(f"Checking pick status for order: {order_number}")
            
            try:
                # Make API request
                api_url = f"{api_host}/api/history/?order_name={order_number}"
                response = requests.get(api_url, timeout=30)
                response.raise_for_status()
                history_data = response.json()
                
                if not history_data:
                    logger.info(f"No history data found for order {order_number}")
                    continue
                
                # Process each history record
                for record in history_data:
                    # Only process records with history_type=1 (confirmed picks)
                    if record.get('history_type') != 1:
                        continue
                        
                    item_name = record.get('item_name')
                    quantity_confirmed = record.get('quantity_confirmed')
                    user = record.get('user')

                    if not all([item_name, quantity_confirmed is not None]):
                        logger.warning(f"Incomplete data in record for order {order_number}: {record}")
                        continue
                    
                    # Update the order line with actual quantity
                    updated = OrderData.objects.filter(
                        order_number=order_number,
                        item=item_name,
                        sent_status=1
                    ).update(
                        actual_qty=quantity_confirmed,
                        sent_status=3,  # Mark as picked
                        user=user
                    )
                    
                    if updated:
                        logger.info(f"Updated order {order_number}, item {item_name}: "
                                  f"actual_qty={quantity_confirmed}, status=3")
                    else:
                        logger.warning(f"No matching order found for {order_number}, item {item_name}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API error checking pick status for order {order_number}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_pick_status task: {str(e)}", exc_info=True)
        
    logger.info("="*80)
    return "Pick status check completed" 