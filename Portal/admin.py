from django.contrib import admin
from .models import UserProfile, OrderData, MasterInventory, TaskConfig
from django.utils import timezone

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

@admin.register(TaskConfig)
class TaskConfigAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'is_enabled', 'frequency', 'last_run', 'next_run', 'updated_at')
    list_filter = ('is_enabled', 'task_name')
    search_fields = ('task_name',)
    readonly_fields = ('last_run', 'next_run', 'created_at', 'updated_at')
    ordering = ('task_name',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('task_name',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            # Set initial last_run to now for enabled tasks
            if obj.is_enabled:
                obj.last_run = timezone.now()
        super().save_model(request, obj, form, change)
