# Generated by Django 4.2.1 on 2023-05-28 22:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_alter_customer_options_remove_customer_email_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customer',
            options={'ordering': ['user__first_name', 'user__last_name'], 'permissions': [('view_history', 'Can view history')]},
        ),
    ]
