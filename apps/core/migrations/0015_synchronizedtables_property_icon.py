# Generated by Django 3.2.8 on 2022-07-27 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_synchronizedtables_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='property_icon',
            field=models.TextField(blank=True, null=True, verbose_name='property icon url'),
        ),
    ]