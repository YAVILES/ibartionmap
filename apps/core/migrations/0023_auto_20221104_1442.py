# Generated by Django 3.2.8 on 2022-11-04 18:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_synchronizedtables_table_origin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synchronizedtables',
            name='property_icon',
        ),
        migrations.RemoveField(
            model_name='synchronizedtables',
            name='property_latitude',
        ),
        migrations.RemoveField(
            model_name='synchronizedtables',
            name='property_longitude',
        ),
    ]
