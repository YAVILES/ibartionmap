# Generated by Django 3.2.8 on 2022-11-07 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_synchronizedtables_tables'),
    ]

    operations = [
        migrations.AlterField(
            model_name='synchronizedtables',
            name='table',
            field=models.CharField(max_length=100, verbose_name='table'),
        ),
    ]
