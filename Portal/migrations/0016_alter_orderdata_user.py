# Generated by Django 5.0.13 on 2025-03-27 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0015_alter_orderdata_bin_location_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdata',
            name='user',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
