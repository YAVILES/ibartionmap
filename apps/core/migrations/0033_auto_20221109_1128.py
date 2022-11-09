# Generated by Django 3.2.8 on 2022-11-09 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_auto_20221109_1115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='field_latitude',
            field=models.JSONField(default=dict, verbose_name='property latitude'),
        ),
        migrations.AlterField(
            model_name='marker',
            name='field_longitude',
            field=models.JSONField(default=dict, verbose_name='property longitude'),
        ),
    ]
