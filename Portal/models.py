from django.db import models
from django.contrib.auth.models import User

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
