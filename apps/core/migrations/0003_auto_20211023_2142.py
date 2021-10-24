# Generated by Django 3.2.8 on 2021-10-24 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_synchronizedtables_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='lat',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='synchronizedtables',
            name='lon',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='synchronizedtables',
            name='show_on_map',
            field=models.BooleanField(default=False),
        ),
    ]
