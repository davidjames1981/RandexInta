# Generated by Django 5.0.13 on 2025-03-28 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0017_orderdata_order_line'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdata',
            name='inserted_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
