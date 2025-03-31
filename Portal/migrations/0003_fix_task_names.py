from django.db import migrations

def fix_task_names(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    
    # Remove the process_staging_orders task
    TaskConfig.objects.filter(task_name='process_staging_orders').delete()
    
    # Update any incorrect task names
    task_name_mapping = {
        'Portal.tasks.check_pick_status.check_pick_status': 'Portal.tasks.check_pick_status',
        'Portal.tasks.api_inventory.api_inventory_creation': 'Portal.tasks.api_inventory.api_inventory_creation',
    }
    
    for old_name, new_name in task_name_mapping.items():
        TaskConfig.objects.filter(task_name=old_name).update(task_name=new_name)

def reverse_fix_task_names(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    
    # Restore the process_staging_orders task
    TaskConfig.objects.create(
        task_name='process_staging_orders',
        frequency=10,
        is_enabled=True
    )
    
    # Restore any incorrect task names
    task_name_mapping = {
        'Portal.tasks.check_pick_status': 'Portal.tasks.check_pick_status.check_pick_status',
        'Portal.tasks.api_inventory.api_inventory_creation': 'Portal.tasks.api_inventory.api_inventory_creation',
    }
    
    for new_name, old_name in task_name_mapping.items():
        TaskConfig.objects.filter(task_name=new_name).update(task_name=old_name)

class Migration(migrations.Migration):
    dependencies = [
        ('Portal', '0002_update_task_names'),
    ]

    operations = [
        migrations.RunPython(fix_task_names, reverse_fix_task_names),
    ] 