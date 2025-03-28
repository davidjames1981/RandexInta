from django.contrib import admin
from django.utils import timezone
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import UserProfile, OrderData, MasterInventory, TaskConfig, WarehouseLocation
from django.contrib.admin import AdminSite

# Custom Admin Site
class PortalAdminSite(AdminSite):
    site_header = 'Portal Management System'
    site_title = 'Portal Admin'
    index_title = 'Portal Administration'
    
    # Custom admin template
    index_template = 'admin/custom_index.html'
    login_template = 'admin/custom_login.html'

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site, organized into Settings and Operations sections.
        """
        app_dict = self._build_app_dict(request)
        
        # Create Settings and Operations sections
        settings_models = ['UserProfile', 'WarehouseLocation']
        
        settings_section = {
            'name': 'Settings',
            'app_label': 'settings',
            'app_url': '/admin/',
            'has_module_perms': True,
            'models': []
        }
        
        operations_section = {
            'name': 'Operations',
            'app_label': 'operations',
            'app_url': '/admin/',
            'has_module_perms': True,
            'models': []
        }
        
        # Organize models into sections
        for app_label in app_dict:
            app = app_dict[app_label]
            for model in app['models']:
                if model['object_name'] in settings_models:
                    settings_section['models'].append(model)
                else:
                    operations_section['models'].append(model)
        
        # Return organized sections
        app_list = []
        if settings_section['models']:
            app_list.append(settings_section)
        if operations_section['models']:
            app_list.append(operations_section)
            
        return app_list

# Create custom admin site instance
portal_admin_site = PortalAdminSite(name='portal_admin')

# Resources for Import/Export
class OrderDataResource(resources.ModelResource):
    class Meta:
        model = OrderData
        import_id_fields = ('id',)
        fields = ('id', 'order_number', 'transaction_type', 'item', 'quantity', 'actual_qty', 
                 'processed_at', 'file_name', 'sent_status', 'api_error', 'user', 
                 'wms_location', 'bin_location', 'order_line')

class MasterInventoryResource(resources.ModelResource):
    class Meta:
        model = MasterInventory
        import_id_fields = ('item',)
        fields = ('item', 'description', 'uom', 'cus1', 'cus2', 'cus3', 'status')

class WarehouseLocationResource(resources.ModelResource):
    class Meta:
        model = WarehouseLocation
        import_id_fields = ('id',)
        fields = ('id', 'wms_location', 'cn_bin')

# Settings Models
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'location', 'birth_date', 'avatar'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

class WarehouseLocationAdmin(ImportExportModelAdmin):
    resource_class = WarehouseLocationResource
    list_display = ('wms_location', 'cn_bin')
    search_fields = ('wms_location', 'cn_bin')
    list_filter = ('wms_location',)
    fieldsets = (
        ('Location Information', {
            'fields': ('wms_location', 'cn_bin'),
            'classes': ('wide',)
        }),
    )

# Operational Models
class OrderDataAdmin(ImportExportModelAdmin):
    resource_class = OrderDataResource
    list_display = ('order_number', 'transaction_type', 'item', 'quantity', 'actual_qty', 'sent_status', 'processed_at')
    list_filter = ('sent_status', 'transaction_type', 'processed_at')
    search_fields = ('order_number', 'item', 'user')
    readonly_fields = ('processed_at',)
    ordering = ('-processed_at',)
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'transaction_type', 'item', 'quantity', 'actual_qty'),
            'classes': ('wide',)
        }),
        ('Status & Processing', {
            'fields': ('sent_status', 'processed_at', 'api_error'),
            'classes': ('wide',)
        }),
        ('Location Information', {
            'fields': ('wms_location', 'bin_location', 'order_line'),
            'classes': ('wide',)
        }),
        ('Additional Information', {
            'fields': ('file_name', 'user'),
            'classes': ('collapse',)
        }),
    )

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
            'classes': ('wide',)
        }),
        ('Custom Fields', {
            'fields': ('cus1', 'cus2', 'cus3'),
            'classes': ('wide',)
        }),
        ('Import Information', {
            'fields': ('status', 'import_timestamp'),
            'classes': ('collapse',)
        }),
    )

class TaskConfigAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'is_enabled', 'frequency', 'last_run', 'next_run', 'updated_at')
    list_filter = ('is_enabled', 'task_name')
    search_fields = ('task_name',)
    readonly_fields = ('last_run', 'next_run', 'created_at', 'updated_at')
    ordering = ('task_name',)
    fieldsets = (
        ('Task Configuration', {
            'fields': ('task_name', 'is_enabled', 'frequency'),
            'classes': ('wide',)
        }),
        ('Execution Information', {
            'fields': ('last_run', 'next_run', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('task_name',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change and obj.is_enabled:
            obj.last_run = timezone.now()
        super().save_model(request, obj, form, change)

# Register models with custom admin site
portal_admin_site.register(UserProfile, UserProfileAdmin)
portal_admin_site.register(WarehouseLocation, WarehouseLocationAdmin)
portal_admin_site.register(OrderData, OrderDataAdmin)
portal_admin_site.register(MasterInventory, MasterInventoryAdmin)
portal_admin_site.register(TaskConfig, TaskConfigAdmin)
