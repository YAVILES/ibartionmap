# Generated by Django 3.2.8 on 2022-11-04 19:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_synchronizedtablesdata_relations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='relationstable',
            name='two_dimensional',
        ),
    ]