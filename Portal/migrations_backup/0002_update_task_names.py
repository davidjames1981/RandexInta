from django.db import migrations

def update_task_names(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    
    # Define the mapping of old task names to new task names
    task_name_mapping = {
        'process_excel_files': 'Portal.tasks.import_order.process_excel_files',
        'create_api_orders': 'Portal.tasks.api_order_creation.create_api_orders',
        'check_pick_status': 'Portal.tasks.check_pick_status',
        'process_inventory_files': 'Portal.tasks.import_inventory.process_inventory_files',
        'api_inventory_creation': 'Portal.tasks.api_inventory.api_inventory_creation',
        'export_completed_orders': 'Portal.tasks.export_order.export_completed_orders',
        'process_demo_orders': 'Portal.tasks.vlm_demo.process_demo_orders',
    }
    
    # Update each task's name
    for old_name, new_name in task_name_mapping.items():
        TaskConfig.objects.filter(task_name=old_name).update(task_name=new_name)

def reverse_task_names(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    
    # Define the reverse mapping of new task names to old task names
    task_name_mapping = {
        'Portal.tasks.import_order.process_excel_files': 'process_excel_files',
        'Portal.tasks.api_order_creation.create_api_orders': 'create_api_orders',
        'Portal.tasks.check_pick_status': 'check_pick_status',
        'Portal.tasks.import_inventory.process_inventory_files': 'process_inventory_files',
        'Portal.tasks.api_inventory.api_inventory_creation': 'api_inventory_creation',
        'Portal.tasks.export_order.export_completed_orders': 'export_completed_orders',
        'Portal.tasks.vlm_demo.process_demo_orders': 'process_demo_orders',
    }
    
    # Update each task's name back to the old format
    for new_name, old_name in task_name_mapping.items():
        TaskConfig.objects.filter(task_name=new_name).update(task_name=old_name)

class Migration(migrations.Migration):
    dependencies = [
        ('Portal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_task_names, reverse_task_names),
    ] 