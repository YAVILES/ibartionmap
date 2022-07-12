import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.core.models import ModelBase, SynchronizedTables


class Connection(ModelBase):
    DB = 0
    API = 1
    TYPES = (
        (DB, "Base de Datos"),
        # (API, "API")
    )
    MySQL = 'MySQL'
    DATABASES_ORIGIN = (
        (MySQL, "MySQL"),
    )
    description = models.CharField(max_length=255, verbose_name=_('description'), null=True, blank=None)
    host = models.CharField(max_length=255, verbose_name=_('host connection'), null=True, blank=None)
    type = models.SmallIntegerField(verbose_name=_('type'), default=DB, choices=TYPES)
    database_origin = models.CharField(
        max_length=10,
        verbose_name=_('database origin'),
        default=MySQL,
        choices=DATABASES_ORIGIN
    )
    database_name = models.CharField(max_length=255, verbose_name=_('database name'), null=True, blank=None)
    database_username = models.CharField(max_length=255, verbose_name=_('database username'), null=True, blank=None)
    database_password = models.CharField(max_length=255, verbose_name=_('database password'), null=True, blank=None)
    database_port = models.IntegerField(verbose_name=_('database port'), null=True, blank=None)
    info_to_sync = models.JSONField(default=list)
    info_to_sync_selected = models.JSONField(default=list)
    periodic_task = models.ForeignKey(
        PeriodicTask,
        verbose_name=_('periodic task'),
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    every_interval = models.IntegerField(verbose_name=_('every interval'),  blank=None, default=10)
    period_interval = models.CharField(
        max_length=25, verbose_name=_('period interval'), default=IntervalSchedule.SECONDS, blank=None
    )
    is_active = models.BooleanField(verbose_name=_('is active'), default=True)

    def __str__(self):
        if self.type == Connection.DB:
            return self.description + " " + self.database_origin + " ("+str(self.id) + ")"
        else:
            return self.description + " (" + str(self.id) + ")"


def post_save_connection(sender, instance: Connection, **kwargs):
    created = kwargs['created']
    if created:
        if instance.type == Connection.DB and instance.info_to_sync_selected:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=instance.every_interval,
                period=instance.period_interval
            )
            periodic_task: PeriodicTask = PeriodicTask.objects.create(
                interval=schedule,
                name='Synchronization with connection ' + instance.description,
                task='sync_with_connection',
                args=json.dumps([str(instance.id)]),
                enabled=instance.is_active
            )
            instance.periodic_task_id = periodic_task.id
            instance.save(update_fields=["periodic_task_id"])
    else:
        if instance.type == Connection.DB and instance.info_to_sync_selected:
            for table in instance.info_to_sync_selected:
                try:
                    synchronized_table = SynchronizedTables.objects.get(connection_id=instance.id, table=table)
                    if not synchronized_table.is_active:
                        synchronized_table.is_active = True
                        synchronized_table.save(update_fields=['is_active'])
                except ObjectDoesNotExist:
                    for info in instance.info_to_sync:
                        if info.get('table') == table:
                            fields = info.get('fields')
                            for field in fields:
                                field["selected"] = False
                            break
                    synchronized_table = SynchronizedTables.objects.create(
                        table=table,
                        alias="",
                        fields=fields,
                        data=[],
                        show_on_map=False,
                        property_latitude=None,
                        property_longitude=None,
                        connection=instance
                    )
            SynchronizedTables.objects.filter(
                connection_id=instance.id
            ).exclude(
                table__in=instance.info_to_sync_selected
            ).update(is_active=False)
            try:
                periodic_task: PeriodicTask = PeriodicTask.objects.get(
                    id=instance.periodic_task_id
                )
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=instance.every_interval,
                    period=instance.period_interval
                )
                periodic_task.interval = schedule
                periodic_task.enabled = instance.is_active
                periodic_task.save(update_fields=['enabled', 'interval'])
            except ObjectDoesNotExist:
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=instance.every_interval,
                    period=instance.period_interval
                )
                periodic_task = PeriodicTask.objects.create(
                    interval=schedule,
                    name='Synchronization with connection ' + instance.description,
                    task='sync_with_connection',
                    args=json.dumps([str(instance.id)]),
                    enabled=instance.is_active
                )
                instance.periodic_task_id = periodic_task.id
                instance.save(update_fields=["periodic_task_id"])


post_save.connect(post_save_connection, sender=Connection)
