from django.db import migrations

def add_vlm_demo_task(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    
    # Create the VLM demo task if it doesn't exist
    TaskConfig.objects.get_or_create(
        task_name='Portal.tasks.vlm_demo.process_demo_orders',
        defaults={
            'is_enabled': True,
            'frequency': 10,  # 10 seconds frequency
        }
    )

def remove_vlm_demo_task(apps, schema_editor):
    TaskConfig = apps.get_model('Portal', 'TaskConfig')
    TaskConfig.objects.filter(task_name='Portal.tasks.vlm_demo.process_demo_orders').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0002_update_task_names'),
    ]

    operations = [
        migrations.RunPython(add_vlm_demo_task, remove_vlm_demo_task),
    ] 