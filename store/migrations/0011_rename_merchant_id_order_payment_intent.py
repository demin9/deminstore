# Generated by Django 4.1.7 on 2023-04-26 01:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_alter_customer_options_alter_product_inventory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='merchant_id',
            new_name='payment_intent',
        ),
    ]
