# Generated by Django 3.2.8 on 2022-06-22 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_relationstable_two_dimensional'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='fields',
            field=models.JSONField(default=list),
        ),
    ]