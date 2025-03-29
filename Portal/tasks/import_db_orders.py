import os
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from ..models import OrderData, WarehouseLocation, TaskConfig
import pyodbc
from datetime import datetime
from urllib.parse import urlparse
import re

# Set up logger with the exact name that matches the logging config
logger = logging.getLogger('db_order_import')

def parse_db_url(db_url):
    """Parse database URL into connection parameters"""
    parsed = urlparse(db_url)
    if parsed.scheme not in ['mssql', 'sqlserver']:
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
    
    # Extract credentials from netloc
    auth, host = parsed.netloc.split('@')
    user, password = auth.split(':')
    
    # Extract database name from path
    db_name = parsed.path.lstrip('/')
    
    # Extract port from host if present
    host_parts = host.split(':')
    server = host_parts[0]
    port = host_parts[1] if len(host_parts) > 1 else '1433'
    
    return {
        'server': server,
        'port': port,
        'database': db_name,
        'username': user,
        'password': password
    }

def get_db_connection():
    """Create and return a connection to the staging database"""
    try:
        # Get connection URL from environment variables
        staging_db_url = os.getenv('STAGING_DATABASE_URL')
        
        if not staging_db_url:
            raise ValueError("Missing STAGING_DATABASE_URL in environment variables")
        
        # Parse the connection URL
        conn_params = parse_db_url(staging_db_url)
        
        # Create connection string
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={conn_params['server']},{conn_params['port']};"
            f"DATABASE={conn_params['database']};"
            f"UID={conn_params['username']};"
            f"PWD={conn_params['password']}"
        )
        
        # Create connection
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to staging database: {str(e)}")
        raise

@shared_task(name='Portal.tasks.import_db_orders')
def process_db_orders():
    """Process orders from the staging database"""
    try:
        logger.info("="*80)
        logger.info("Starting database order import task")

        # Get task configuration
        task_config = TaskConfig.objects.filter(task_name='Portal.tasks.import_db_orders').first()
        if not task_config:
            logger.error("Task configuration not found")
            return "Error: Task configuration not found"

        # Get the last run timestamp or use a default if this is the first run
        last_processed = task_config.last_run
        if not last_processed:
            last_processed = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        logger.info(f"Last processed timestamp from TaskConfig: {last_processed}")
        
        # Update task configuration with current run time
        current_run_time = timezone.now()
        task_config.last_run = current_run_time
        task_config.next_run = current_run_time + timezone.timedelta(seconds=task_config.frequency)
        task_config.save()
        logger.info(f"Updated task configuration - Last run: {task_config.last_run}, Next run: {task_config.next_run}")
        
        # Create a location lookup dictionary for faster lookups
        location_lookup = {loc.wms_location: loc.cn_bin for loc in WarehouseLocation.objects.all()}
        logger.info(f"Loaded {len(location_lookup)} warehouse locations for lookup")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Log connection details for debugging
            logger.info(f"Connected to database: {conn.getinfo(pyodbc.SQL_DATABASE_NAME)}")
            logger.info(f"Using table: {os.getenv('STAGING_ORDERS_TABLE', 'orders')}")
            
            # Get column mapping from environment variables
            column_mapping = {
                'order_number': os.getenv('STAGING_ORDER_NUMBER_COL', 'order_number'),
                'transaction_type': os.getenv('STAGING_TRANSACTION_TYPE_COL', 'transaction_type'),
                'item': os.getenv('STAGING_ITEM_COL', 'item'),
                'quantity': os.getenv('STAGING_QUANTITY_COL', 'quantity'),
                'location': os.getenv('STAGING_LOCATION_COL', 'location'),
                'order_line': os.getenv('STAGING_ORDER_LINE_COL', 'order_line'),
                'created_at': os.getenv('STAGING_CREATED_AT_COL', 'created_at')
            }
            
            # Format the last_processed timestamp for SQL Server
            last_processed_str = last_processed.strftime('%Y-%m-%d %H:%M:%S')
            
            # First, get all orders created after last_processed
            orders_query = f"""
                SELECT DISTINCT {column_mapping['order_number']} as order_number
                FROM {os.getenv('STAGING_ORDERS_TABLE', 'orders')}
                WHERE {column_mapping['created_at']} > ?
                ORDER BY {column_mapping['order_number']}
            """
            
            logger.info(f"Executing query: {orders_query}")
            logger.info(f"With last_processed parameter: {last_processed_str}")
            
            cursor.execute(orders_query, (last_processed_str,))
            orders = cursor.fetchall()
            
            if not orders:
                logger.info("No new orders found in staging database")
                return "No new orders to process"
            
            logger.info(f"Found {len(orders)} orders to process")
            
            processed_count = 0
            error_count = 0
            skipped_count = 0
            
            # Process each order
            for order in orders:
                order_number = order.order_number
                logger.info(f"Processing order: {order_number}")
                
                # Check if order already exists
                if OrderData.objects.filter(order_number=order_number, file_name='DB_IMPORT').exists():
                    logger.info(f"Order {order_number} already exists in the system, skipping...")
                    skipped_count += 1
                    continue
                
                # Get all lines for this order
                lines_query = f"""
                    SELECT 
                        {column_mapping['order_number']} as order_number,
                        {column_mapping['transaction_type']} as transaction_type,
                        {column_mapping['item']} as item,
                        {column_mapping['quantity']} as quantity,
                        {column_mapping['location']} as location,
                        {column_mapping['order_line']} as order_line,
                        {column_mapping['created_at']} as created_at
                    FROM {os.getenv('STAGING_ORDERS_TABLE', 'orders')}
                    WHERE {column_mapping['order_number']} = ?
                    ORDER BY {column_mapping['order_line']}
                """
                
                cursor.execute(lines_query, (order_number,))
                order_lines = cursor.fetchall()
                
                if not order_lines:
                    logger.warning(f"No lines found for order {order_number}")
                    error_count += 1
                    continue
                
                # Log order lines for debugging
                logger.info(f"Found {len(order_lines)} lines for order {order_number}")
                for line in order_lines:
                    logger.debug(f"Line data: {line}")
                
                # Check if all lines are complete (no missing line numbers)
                line_numbers = [line.order_line for line in order_lines]
                expected_lines = set(range(1, max(line_numbers) + 1))
                missing_lines = expected_lines - set(line_numbers)
                
                if missing_lines:
                    logger.warning(f"Order {order_number} has missing lines: {missing_lines}")
                    error_count += 1
                    continue
                
                # Process all lines for this order
                try:
                    for line in order_lines:
                        # Get the location value and lookup bin location
                        location_value = line.location
                        bin_location = location_lookup.get(location_value) if location_value else None
                        
                        # Map database columns to model fields
                        order_data = {
                            'order_number': line.order_number,
                            'transaction_type': line.transaction_type,
                            'item': line.item,
                            'quantity': line.quantity,
                            'sent_status': 0,
                            'file_name': 'DB_IMPORT',
                            'wms_location': location_value,
                            'bin_location': bin_location,
                            'order_line': line.order_line,
                            'processed_at': timezone.now(),
                        }
                        
                        # Create order line
                        order = OrderData.objects.create(**order_data)
                        logger.info(f"Created order line: {order.order_number} - Line {order.order_line} - {order.item} (Qty: {order.quantity}, Location: {location_value}, Bin: {bin_location})")
                    
                    processed_count += 1
                    logger.info(f"Successfully processed complete order {order_number} with {len(order_lines)} lines")
                    
                except Exception as order_error:
                    logger.error(f"Error processing order {order_number}: {str(order_error)}")
                    logger.error(f"Order lines data: {[line.__dict__ for line in order_lines]}")
                    error_count += 1
            
            logger.info(f"Task completed. Processed {processed_count} complete orders, skipped {skipped_count} duplicates, with {error_count} errors")
            return f"Processed {processed_count} complete orders, skipped {skipped_count} duplicates, with {error_count} errors"
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
                
    except Exception as e:
        logger.error(f"Critical error in process_db_orders task: {str(e)}")
        logger.exception("Full traceback:")
        return f"Error: {str(e)}" 