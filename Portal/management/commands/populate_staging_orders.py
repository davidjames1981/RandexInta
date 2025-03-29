from django.core.management.base import BaseCommand
from Portal.models import StagingOrder
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Populate staging orders table with example data'

    def handle(self, *args, **options):
        # Clear existing data
        StagingOrder.objects.all().delete()
        
        # Example items and locations
        items = ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004', 'ITEM005']
        locations = ['LOC001', 'LOC002', 'LOC003', 'LOC004', 'LOC005']
        
        # Generate orders
        order_numbers = [f'ORD{str(i).zfill(3)}' for i in range(1, 6)]
        transaction_types = ['PICK', 'PUT']
        
        # Create orders with multiple lines
        for order_number in order_numbers:
            # Random number of lines per order (2-5)
            num_lines = random.randint(2, 5)
            
            # Create lines for this order
            for line_number in range(1, num_lines + 1):
                StagingOrder.objects.create(
                    order_number=order_number,
                    transaction_type=random.choice(transaction_types),
                    item=random.choice(items),
                    quantity=random.randint(1, 10),
                    location=random.choice(locations),
                    order_line=line_number,
                    created_at=datetime.now() - timedelta(hours=random.randint(0, 24))
                )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(order_numbers)} orders with multiple lines'))
        
        # Display the created data
        self.stdout.write('\nCreated Orders:')
        for order in StagingOrder.objects.all().order_by('order_number', 'order_line'):
            self.stdout.write(
                f'Order: {order.order_number}, Line: {order.order_line}, '
                f'Type: {order.transaction_type}, Item: {order.item}, '
                f'Qty: {order.quantity}, Location: {order.location}'
            ) 