# Generated by Django 3.2.8 on 2022-09-14 02:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20220913_2245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='synchronizedtablesdata',
            name='table',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='data', to='core.synchronizedtables', verbose_name='table'),
        ),
    ]
