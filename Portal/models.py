from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class OrderData(models.Model):
    id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=50)
    item = models.CharField(max_length=50)
    quantity = models.IntegerField()
    actual_qty = models.IntegerField(null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    sent_status = models.IntegerField(default=0)
    api_error = models.TextField(null=True, blank=True)
    user= models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.order_number} - {self.item}"

    class Meta:
        db_table = 'order_data'

class MasterInventory(models.Model):
    # Mandatory fields
    item = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)
    uom = models.CharField(max_length=10)
    
    # Optional custom fields
    cus1 = models.CharField(max_length=255, null=True, blank=True)
    cus2 = models.CharField(max_length=255, null=True, blank=True)
    cus3 = models.CharField(max_length=255, null=True, blank=True)
    
    # Import tracking fields
    import_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'masterinventory_data'
        verbose_name = 'Master Inventory'
        verbose_name_plural = 'Master Inventory'
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['status']),
            models.Index(fields=['import_timestamp'])
        ]
    
    def __str__(self):
        return f"{self.item} - {self.description}"

class TaskConfig(models.Model):
    TASK_CHOICES = [
        ('Portal.tasks.import_order.process_excel_files', 'Process Excel Files'),
        ('Portal.tasks.api_order_creation.create_api_orders', 'Create API Orders'),
        ('Portal.tasks.check_pick_status', 'Check Pick Status'),
        ('Portal.tasks.import_inventory.process_inventory_files', 'Process Inventory Files'),
        ('Portal.tasks.api_inventory.api_inventory_creation', 'Create Inventory API'),
    ]

    task_name = models.CharField(max_length=255, choices=TASK_CHOICES, unique=True)
    is_enabled = models.BooleanField(default=True)
    frequency = models.IntegerField(default=60, help_text="Frequency in seconds")
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task Configuration'
        verbose_name_plural = 'Task Configurations'

    def __str__(self):
        status = 'Enabled' if self.is_enabled else 'Disabled'
        frequency = f'{self.frequency}s' if self.frequency else 'Not set'
        return f"{self.get_task_name_display()} ({status}, {frequency})"

    def save(self, *args, **kwargs):
        # Update next_run based on frequency
        if self.last_run and self.is_enabled:
            self.next_run = self.last_run + timedelta(seconds=self.frequency)
        super().save(*args, **kwargs)
