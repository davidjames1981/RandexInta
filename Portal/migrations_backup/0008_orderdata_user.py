# Generated by Django 5.0.13 on 2025-03-23 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Portal', '0007_rename_portal_mast_item_2d1a7d_idx_masterinven_item_fe0ce4_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdata',
            name='user',
            field=models.TextField(blank=True, null=True),
        ),
    ]
