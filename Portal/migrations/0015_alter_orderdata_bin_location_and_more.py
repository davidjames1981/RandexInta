# Generated by Django 5.0.13 on 2025-03-27 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0014_orderdata_bin_location_orderdata_wms_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdata',
            name='bin_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='orderdata',
            name='wms_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
