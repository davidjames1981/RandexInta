from django.core.management.base import BaseCommand
from Portal.models import OrderData

class Command(BaseCommand):
    help = 'Check order status in the database'

    def handle(self, *args, **options):
        # Get counts for different statuses
        total_orders = OrderData.objects.count()
        pending_orders = OrderData.objects.filter(sent_status=0).count()
        sent_orders = OrderData.objects.filter(sent_status=1).count()
        error_orders = OrderData.objects.filter(sent_status=99).count()

        # Get pending orders grouped by order number
        pending_groups = OrderData.objects.filter(sent_status=0).values('order_number').distinct()
        
        self.stdout.write('\nOrder Statistics:')
        self.stdout.write(f'Total Orders: {total_orders}')
        self.stdout.write(f'Pending Orders (status=0): {pending_orders}')
        self.stdout.write(f'Sent Orders (status=1): {sent_orders}')
        self.stdout.write(f'Error Orders (status=99): {error_orders}')
        
        if pending_groups:
            self.stdout.write('\nPending Orders:')
            for group in pending_groups:
                order_number = group['order_number']
                lines = OrderData.objects.filter(order_number=order_number, sent_status=0)
                self.stdout.write(f'\nOrder Number: {order_number}')
                self.stdout.write(f'Number of Lines: {lines.count()}')
                for line in lines:
                    self.stdout.write(f'  - Item: {line.item}, Quantity: {line.quantity}') 