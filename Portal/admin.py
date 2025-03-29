from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, TaskConfig, OrderData, MasterInventory, WarehouseLocation
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.management import call_command
import os
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def get_role(self, obj):
        if obj.is_superuser:
            return "Superuser"
        elif obj.is_staff:
            return "Staff"
        else:
            return "User"
    get_role.short_description = 'Role'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

@admin.register(TaskConfig)
class TaskConfigAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'is_enabled', 'frequency', 'last_run', 'next_run')
    list_filter = ('is_enabled',)
    readonly_fields = ('last_run', 'next_run', 'created_at', 'updated_at')
    search_fields = ('task_name',)
    ordering = ('task_name',)
    fieldsets = (
        ('Task Configuration', {
            'fields': ('task_name', 'is_enabled', 'frequency'),
            'classes': ('wide',)
        }),
        ('Timing Information', {
            'fields': ('last_run', 'next_run', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class OrderDataResource(resources.ModelResource):
    class Meta:
        model = OrderData
        fields = ('order_number', 'transaction_type', 'item', 'quantity', 'actual_qty', 
                 'processed_at', 'file_name', 'sent_status', 'api_error', 'user', 
                 'wms_location', 'bin_location', 'order_line', 'shortage_qty')

class OrderDataAdmin(ImportExportModelAdmin):
    resource_class = OrderDataResource
    list_display = ('order_number', 'transaction_type', 'item', 'quantity', 'actual_qty', 'get_status_display', 'processed_at')
    list_filter = ('sent_status', 'transaction_type', 'processed_at')
    search_fields = ('order_number', 'item', 'user')
    readonly_fields = ('processed_at', 'inserted_date')
    ordering = ('-processed_at',)

    def get_status_display(self, obj):
        status_map = {
            0: 'Imported',
            1: 'Sent',
            3: 'Complete',
            4: 'Exported',
            99: 'Processing'
        }
        if obj.sent_status is None:
            return 'New'
        return status_map.get(obj.sent_status, str(obj.sent_status))
    get_status_display.short_description = 'Status'

    fieldsets = (
        (None, {
            'fields': (
                'order_number', 'transaction_type', 'item', 'quantity', 'actual_qty',
                'sent_status', 'processed_at', 'api_error',
                'wms_location', 'bin_location', 'order_line',
                'file_name', 'user', 'shortage_qty', 'inserted_date'
            )
        }),
    )

class MasterInventoryResource(resources.ModelResource):
    class Meta:
        model = MasterInventory
        fields = ('item', 'description', 'uom', 'cus1', 'cus2', 'cus3', 'status', 'import_timestamp')

class MasterInventoryAdmin(ImportExportModelAdmin):
    resource_class = MasterInventoryResource
    list_display = ('item', 'description', 'uom', 'status', 'import_timestamp')
    list_filter = ('status', 'import_timestamp')
    search_fields = ('item', 'description')
    readonly_fields = ('import_timestamp',)
    ordering = ('-import_timestamp',)
    fieldsets = (
        ('Item Information', {
            'fields': ('item', 'description', 'uom'),
        }),
        ('Custom Fields', {
            'fields': ('cus1', 'cus2', 'cus3'),
        }),
        ('Import Information', {
            'fields': ('status', 'import_timestamp'),
            'classes': ('collapse',)
        }),
    )

class WarehouseLocationResource(resources.ModelResource):
    class Meta:
        model = WarehouseLocation
        fields = ('wms_location', 'cn_bin')

class WarehouseLocationAdmin(ImportExportModelAdmin):
    resource_class = WarehouseLocationResource
    list_display = ('wms_location', 'cn_bin')
    search_fields = ('wms_location', 'cn_bin')
    list_filter = ('wms_location',)
    fieldsets = (
        ('Location Information', {
            'fields': ('wms_location', 'cn_bin'),
        }),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(OrderData, OrderDataAdmin)
admin.site.register(MasterInventory, MasterInventoryAdmin)
admin.site.register(WarehouseLocation, WarehouseLocationAdmin)