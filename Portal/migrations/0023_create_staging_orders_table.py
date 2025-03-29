# Generated by Django 5.0.13 on 2025-03-29 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0022_add_db_import_task'),
    ]

    operations = [
        migrations.CreateModel(
            name='StagingOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=50)),
                ('transaction_type', models.CharField(max_length=50)),
                ('item', models.CharField(max_length=50)),
                ('quantity', models.IntegerField()),
                ('location', models.CharField(max_length=255, null=True, blank=True)),
                ('order_line', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'staging_orders',
            },
        ),
    ] 