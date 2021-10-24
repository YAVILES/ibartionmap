# Generated by Django 3.2.8 on 2021-10-24 14:03

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20211023_2144'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationsTable',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('property_table_one', models.CharField(max_length=100, verbose_name='property table one')),
                ('property_table_two', models.CharField(max_length=100, verbose_name='property table two')),
                ('table_one', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_one', to='core.synchronizedtables', verbose_name='table one')),
                ('table_two', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_two', to='core.synchronizedtables', verbose_name='table two')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]