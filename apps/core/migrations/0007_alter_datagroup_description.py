# Generated by Django 3.2.8 on 2021-10-24 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20211024_1008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datagroup',
            name='description',
            field=models.CharField(max_length=100, unique=True, verbose_name='description'),
        ),
    ]
