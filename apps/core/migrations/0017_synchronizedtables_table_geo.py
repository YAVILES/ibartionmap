# Generated by Django 3.2.8 on 2022-09-02 17:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20220812_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='synchronizedtables',
            name='table_geo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.synchronizedtables', verbose_name='table geo'),
        ),
    ]
