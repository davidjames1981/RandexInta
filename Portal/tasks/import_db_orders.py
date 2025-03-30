import os
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
import pytz
from ..models import OrderData, WarehouseLocation, TaskConfig
import pyodbc
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Set up logger
logger = logging.getLogger('db_order_import')

@shared_task(name='Portal.tasks.import_db_orders.process_staging_orders')
def process_staging_orders():
    """Process orders from the staging database"""
    try:
        logger.info("="*80)
        logger.info("Starting staging database order import task")

        # Get task configuration
        task_config = TaskConfig.objects.get(task_name='Portal.tasks.import_db_orders.process_staging_orders')
        
        # Update last_run before processing to prevent missing orders during long runs
        current_time = timezone.now()
        last_run = task_config.last_run or datetime(2000, 1, 1, tzinfo=pytz.UTC)
        
        # Convert last_run to naive UTC for SQL Server comparison
        last_run_naive = last_run.astimezone(pytz.UTC).replace(tzinfo=None)
        
        task_config.last_run = current_time
        task_config.next_run = current_time + timedelta(seconds=task_config.frequency)
        task_config.save()
        
        logger.info(f"Processing orders created after: {last_run_naive}")

        # Get staging database connection string from environment
        staging_db_url = os.getenv('STAGING_DATABASE_URL')
        if not staging_db_url:
            logger.error("STAGING_DATABASE_URL environment variable is not set")
            return "Staging database URL not configured"

        # Parse connection string
        parsed = urlparse(staging_db_url)
        if parsed.scheme != 'mssql':
            logger.error(f"Unsupported database type: {parsed.scheme}")
            return "Unsupported database type"

        # Extract connection parameters
        server = parsed.hostname
        database = parsed.path.lstrip('/')
        username = parsed.username
        password = parsed.password

        # Build connection string for pyodbc
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        try:
            # Connect to staging database
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            logger.info(f"Connected to staging database: {database} on {server}")

            # Get column mappings from environment variables
            table_name = os.getenv('STAGING_ORDERS_TABLE', 'Portal_staging_orders')
            order_number_col = os.getenv('STAGING_ORDER_NUMBER_COL', 'order_number')
            transaction_type_col = os.getenv('STAGING_TRANSACTION_TYPE_COL', 'transaction_type')
            item_col = os.getenv('STAGING_ITEM_COL', 'item')
            quantity_col = os.getenv('STAGING_QUANTITY_COL', 'quantity')
            location_col = os.getenv('STAGING_LOCATION_COL', 'location')
            order_line_col = os.getenv('STAGING_ORDER_LINE_COL', 'order_line')
            created_at_col = os.getenv('STAGING_CREATED_AT_COL', 'created_at')

            # Query for new orders
            query = f"""
                SELECT 
                    {order_number_col},
                    {transaction_type_col},
                    {item_col},
                    {quantity_col},
                    {location_col},
                    {order_line_col},
                    CAST({created_at_col} AS datetime2) as {created_at_col}
                FROM {table_name}
                WHERE CAST({created_at_col} AS datetime2) > ?
                ORDER BY {order_number_col}, {order_line_col}
            """
            
            cursor.execute(query, (last_run_naive,))
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("No new orders found in staging database")
                return "No new orders to process"

            logger.info(f"Found {len(rows)} new orders to process")

            # Get warehouse location mappings
            location_mappings = {
                loc.wms_location: loc.cn_bin 
                for loc in WarehouseLocation.objects.all()
            }

            processed_count = 0
            error_count = 0

            # Process each order
            for row in rows:
                try:
                    order_number, transaction_type, item, quantity, location, order_line, created_at = row
                    
                    # Look up bin location if WMS location exists
                    bin_location = location_mappings.get(location) if location else None
                    
                    # Create order record
                    order_data = {
                        'order_number': order_number,
                        'transaction_type': transaction_type,
                        'item': item,
                        'quantity': quantity,
                        'wms_location': location,
                        'bin_location': bin_location,
                        'order_line': order_line,
                        'sent_status': 0,
                        'file_name': 'DB Import',
                        'processed_at': timezone.now(),
                        'inserted_date': created_at
                    }
                    
                    # Create or update order
                    OrderData.objects.update_or_create(
                        order_number=order_number,
                        order_line=order_line,
                        defaults=order_data
                    )
                    
                    processed_count += 1
                    logger.info(f"Processed order: {order_number} - Line {order_line}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing order {order_number} - Line {order_line}: {str(e)}")
                    logger.exception("Full traceback:")
            
            logger.info(f"Task completed. Processed {processed_count} orders with {error_count} errors")
            return f"Processed {processed_count} orders with {error_count} errors"

        except pyodbc.Error as e:
            logger.error(f"Database error: {str(e)}")
            logger.exception("Full traceback:")
            return f"Database error: {str(e)}"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    except TaskConfig.DoesNotExist:
        logger.error("Task configuration not found")
        return "Task configuration not found"
    except Exception as e:
        logger.error(f"Critical error in process_staging_orders task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 