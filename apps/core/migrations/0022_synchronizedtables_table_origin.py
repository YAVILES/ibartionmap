# Generated by Django 3.2.8 on 2022-11-04 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20221102_0919'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='table_origin',
            field=models.CharField(default=None, max_length=100, null=True, verbose_name='table_origin'),
        ),
    ]