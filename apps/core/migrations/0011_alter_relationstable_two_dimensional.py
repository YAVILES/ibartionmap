# Generated by Django 3.2.8 on 2022-02-02 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_relationstable_two_dimensional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationstable',
            name='two_dimensional',
            field=models.BooleanField(default=False),
        ),
    ]
