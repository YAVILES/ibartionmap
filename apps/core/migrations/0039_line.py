# Generated by Django 3.2.8 on 2023-06-05 21:17

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_auto_20230420_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('origen_field', models.JSONField(default=dict, verbose_name='origin field')),
                ('destination_field', models.JSONField(default=dict, verbose_name='destination field')),
                ('destination_marker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destination_lines', to='core.synchronizedtables', verbose_name='origin marker')),
                ('origin_marker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='origin_lines', to='core.synchronizedtables', verbose_name='origin marker')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
