import os
import time
import json
import requests
from django.core.management.base import BaseCommand
from Portal.models import TransactionLog, VLMDemoState
from Portal.utils.logger import vlm_demo_logger as logger
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs the VLM demo process'

    def handle(self, *args, **options):
        self.stdout.write('Starting VLM demo process...')
        
        while True:
            try:
                # Check if demo mode is enabled
                if not settings.DEMO_MODE_ENABLED:
                    self.stdout.write('Demo mode is disabled in Django settings')
                    time.sleep(5)
                    continue

                # Check if demo is paused
                if VLMDemoState.is_paused():
                    self.stdout.write('VLM demo is paused')
                    time.sleep(5)
                    continue
                
                # Get API configuration
                api_host = os.getenv('API_HOST', 'http://18.135.240.39:8000')
                processor_id = os.getenv('PROCESSOR_ID', 'RX01')
                
                self.stdout.write(f'Configuration - API Host: {api_host}, Processor ID: {processor_id}')
                
                # Step 1: Get orders
                orders_url = f"{api_host}/api/order/?limit=25&offset=0&search=&order_type__in=3,4,6,7,8,9&allocation_status=&status="
                self.stdout.write(f'Fetching orders from: {orders_url}')
                
                response = requests.get(orders_url, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                
                # Extract orders from the results key
                orders = response_data.get('results', [])
                
                if not orders:
                    self.stdout.write('No orders found')
                    time.sleep(10)
                    continue
                
                self.stdout.write(f'Found {len(orders)} orders to process')
                
                # Process one order
                order = orders[0]  # Take the first order
                order_id = order['id']
                order_name = order['name']
                
                self.stdout.write(f'Processing order: {order_name} (ID: {order_id})')
                
                # Skip manual orders
                if 'Manual' in order_name:
                    self.stdout.write(f'Skipping manual order: {order_name}')
                    time.sleep(5)
                    continue
                
                # Log order fetch
                TransactionLog.objects.create(
                    order_id=order_id,
                    order_name=order_name,
                    action='fetch_order',
                    status='success',
                    details=order
                )
                
                # Allocate order
                allocate_url = f"{api_host}/api/order/{order_id}/allocate"
                self.stdout.write(f'Allocating order: {allocate_url}')
                
                response = requests.post(allocate_url, timeout=30)
                response.raise_for_status()
                allocation_result = response.json()
                
                # Log allocation
                TransactionLog.objects.create(
                    order_id=order_id,
                    order_name=order_name,
                    action='allocate_order',
                    status='success',
                    details=allocation_result
                )
                
                # Start order
                start_url = f"{api_host}/api/order/{order_id}/start"
                self.stdout.write(f'Starting order: {start_url}')
                
                response = requests.post(start_url, timeout=30)
                response.raise_for_status()
                start_result = response.json()
                
                # Log start
                TransactionLog.objects.create(
                    order_id=order_id,
                    order_name=order_name,
                    action='start_order',
                    status='success',
                    details=start_result
                )
                
                # Monitor processor status
                max_retries = 10
                retry_count = 0
                
                while retry_count < max_retries:
                    processor_url = f"{api_host}/api/processor/{processor_id}"
                    self.stdout.write(f'Checking processor status: {processor_url}')
                    
                    response = requests.get(processor_url, timeout=30)
                    response.raise_for_status()
                    processor_tasks = response.json()
                    
                    if not processor_tasks:
                        self.stdout.write('No tasks currently processing')
                        break
                    
                    # Process each task
                    for task in processor_tasks:
                        task_id = task['task_id']
                        task_quantity = task['task_quantity']
                        
                        self.stdout.write(f'Found task {task_id} with quantity {task_quantity}')
                        
                        # Wait 15 seconds before completing
                        self.stdout.write('Waiting 15 seconds before completing task')
                        time.sleep(15)
                        
                        # Complete task
                        complete_url = f"{api_host}/api/confirm-from-displaytool"
                        payload = {
                            "task_id": task_id,
                            "quantity_measured": None,
                            "quantity_input": task_quantity,
                            "isContainerFullQ": False
                        }
                        
                        self.stdout.write(f'Completing task: {complete_url}')
                        
                        response = requests.post(complete_url, json=payload, timeout=30)
                        response.raise_for_status()
                        
                        self.stdout.write('Task completed successfully')
                        break  # Process one task at a time
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(5)
                
                self.stdout.write(f'Finished processing order: {order_name}')
                self.stdout.write('='*80)
                
                # Wait before processing next order
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'API error: {str(e)}'))
                logger.exception('API error')
                time.sleep(10)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Critical error: {str(e)}'))
                logger.exception('Critical error')
                time.sleep(10) 