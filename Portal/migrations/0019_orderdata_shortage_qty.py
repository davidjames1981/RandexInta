# Generated by Django 5.0.13 on 2025-03-28 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0018_orderdata_inserted_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdata',
            name='shortage_qty',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
