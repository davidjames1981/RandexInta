import os
import pandas as pd
from celery import shared_task
from Portal.models import OrderData
from Portal.utils.logger import general_logger as logger
from ..utils.folder_setup import get_folder_path

@shared_task(name='Portal.tasks.export_order.export_completed_orders')
def export_completed_orders():
    """
    Task to export completed orders (status=3) to Excel files.
    Creates one file per order and updates status to 4 after successful export.
    """
    logger.info("="*80)
    logger.info("Starting order export task")
    
    try:
        # Get completed orders that haven't been exported yet
        completed_orders = OrderData.objects.filter(
            sent_status=3
        ).values('order_number').distinct()
        
        if not completed_orders:
            logger.info("No completed orders to export")
            return "No orders to export"
            
        export_folder = get_folder_path('export')
        if not export_folder:
            logger.error("Could not get export folder path")
            return "Export folder path not configured"
            
        os.makedirs(export_folder, exist_ok=True)
        logger.info(f"Exporting to folder: {export_folder}")
        
        exported_count = 0
        
        for order in completed_orders:
            order_number = order['order_number']
            logger.info(f"Processing order: {order_number}")
            
            # Get all lines for this order
            order_lines = OrderData.objects.filter(
                order_number=order_number,
                sent_status=3
            ).order_by('order_line')
            
            # Check if all lines in the order are status 3
            total_lines = OrderData.objects.filter(
                order_number=order_number
            ).count()
            
            if order_lines.count() != total_lines:
                logger.info(f"Skipping order {order_number} - not all lines are complete")
                continue
            
            # Define export filename
            export_file = os.path.join(export_folder, f"{order_number}.xlsx")
            
            # Skip if file already exists
            if os.path.exists(export_file):
                logger.info(f"Export already exists for order {order_number}")
                order_lines.update(sent_status=4)
                continue
            
            # Convert to DataFrame
            data = []
            for line in order_lines:
                data.append({
                    'Order Number': line.order_number,
                    'Transaction Type': line.transaction_type,
                    'Item': line.item,
                    'Quantity Requested': line.quantity,
                    'Actual Quantity': line.actual_qty,
                    'Shortage Quantity': line.shortage_qty,
                    'WMS Location': line.wms_location,
                    'Bin Location': line.bin_location,
                    'Order Line': line.order_line,
                    'Processed At': line.processed_at,
                    'File Name': line.file_name,
                    'User': line.user,
                    'API Error': line.api_error,
                })
            
            df = pd.DataFrame(data)
            
            try:
                # Export to Excel
                df.to_excel(export_file, index=False)
                
                # Verify file was created
                if os.path.exists(export_file):
                    logger.info(f"Exported order {order_number} to {export_file}")
                    order_lines.update(sent_status=4)
                    logger.info(f"Updated status to 4 for order {order_number}")
                    exported_count += 1
                else:
                    logger.error(f"Failed to create export file for order {order_number}")
            except Exception as export_error:
                logger.error(f"Error exporting order {order_number}: {str(export_error)}")
                continue
        
        logger.info(f"Export completed. Exported {exported_count} orders")
        return f"Exported {exported_count} orders"
        
    except Exception as e:
        logger.error(f"Error in export_completed_orders task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 