# Generated by Django 3.2.8 on 2022-09-14 21:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_synchronizedtablesdata_table'),
    ]

    operations = [
        migrations.AlterField(
            model_name='synchronizedtablesdata',
            name='table',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data', to='core.synchronizedtables', verbose_name='table'),
        ),
    ]
