# Generated by Django 4.0.3 on 2023-02-27 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imsApp', '0010_invoice_store_alter_store_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storeproduct',
            name='price',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]