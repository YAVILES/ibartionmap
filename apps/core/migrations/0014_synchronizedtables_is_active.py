# Generated by Django 3.2.8 on 2022-07-12 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_synchronizedtables_connection'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
