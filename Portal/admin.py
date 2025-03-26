from django.contrib import admin
from .models import UserProfile, OrderData, MasterInventory

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(OrderData)
class OrderDataAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'transaction_type', 'item', 'quantity', 'sent_status', 'processed_at')
    list_filter = ('sent_status', 'transaction_type', 'processed_at')
    search_fields = ('order_number', 'item')
    readonly_fields = ('processed_at',)
    ordering = ('-processed_at',)

@admin.register(MasterInventory)
class MasterInventoryAdmin(admin.ModelAdmin):
    list_display = ('item', 'description', 'uom', 'status', 'import_timestamp')
    list_filter = ('status', 'import_timestamp')
    search_fields = ('item', 'description')
    readonly_fields = ('import_timestamp',)
    ordering = ('-import_timestamp',)
