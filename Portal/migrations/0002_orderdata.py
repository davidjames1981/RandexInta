# Generated by Django 5.1.7 on 2025-03-22 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField()),
                ('order_number', models.CharField(max_length=50)),
                ('transaction_type', models.CharField(max_length=50)),
                ('item', models.CharField(max_length=50)),
                ('qty', models.IntegerField()),
                ('sent_status', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
                ('file_name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'order_data',
            },
        ),
    ]
