import json
import uuid

from django.db.models.signals import post_save, post_delete
from psycopg2.extras import RealDictCursor
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from sequences import get_next_value

from ibartionmap.utils.functions import connect_with_on_map

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

DAYS = (
    (MONDAY, _('Lunes')),
    (TUESDAY, _('Martes')),
    (WEDNESDAY, _('Miercoles')),
    (THURSDAY, _('Jueves')),
    (FRIDAY, _('Viernes')),
    (SATURDAY, _('Sábado')),
    (SUNDAY, _('Domingo')),
)


def map_virtual(table_id, data, fields, table_geo_id, property_latitude, property_longitude, property_icon):
    d = {}
    for field in fields:
        if field in data.keys():
            d[field] = data[field]
    obj = {}

    try:
        if 'table' in list(d.keys()) and table_geo_id == d['table'] and d[property_latitude] and d[property_longitude]:
            obj["point"] = {
                "longitude": float(d[property_longitude]),
                "latitude": float(d[property_latitude])
            }
        else:
            try:
                if d[property_latitude] and d[property_longitude]:
                    obj["point"] = {
                        "longitude": float(d[property_longitude]),
                        "latitude": float(d[property_latitude])
                    }
                else:
                    obj["point"] = None
            except KeyError:
                if d[property_latitude] and d[property_longitude]:
                    obj["point"] = {
                        "longitude": float(d[property_longitude]),
                        "latitude": float(d[property_latitude])
                    }
                else:
                    obj["point"] = None

        if property_icon and property_icon in list(d.keys()):
            obj[property_icon] = d[property_icon]

        # if user:
        #     if user.is_superuser:
        for data_group in DataGroup.objects.filter(table_id=table_id):
            for field in data_group.properties:
                property_field = field.get('Field')
                if property_field and property_field in list(d.keys()):
                    obj[property_field] = d[property_field]

    except KeyError:
        obj['point'] = None
    return obj


class ModelBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(verbose_name=_('created'), auto_now_add=True)
    updated = models.DateTimeField(verbose_name=_('updated'), auto_now=True)

    class Meta:
        abstract = True


def get_table_repeat_number(table_name: str):
    return get_next_value(table_name)


class SynchronizedTables(ModelBase):
    table_origin = models.CharField(max_length=100, verbose_name=_('table_origin'), default=None, null=True)
    table = models.CharField(max_length=100, verbose_name=_('table'))
    alias = models.CharField(max_length=255, verbose_name=_('alias'))
    fields = models.JSONField(default=list)
    connection = models.ForeignKey(
        'setting.Connection',
        verbose_name=_('connection'),
        on_delete=models.CASCADE,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_virtual = models.BooleanField(default=False)
    relations = models.ManyToManyField(
        'core.RelationsTable',
        related_name=_('relations'),
        verbose_name=_('relations')
    )
    sql = models.TextField(blank=True, null=True)
    tables = models.ManyToManyField(
        'self',
        related_name=_('tables'),
        verbose_name=_('tables')
    )

    class Meta:
        verbose_name = _('synchronized table')
        verbose_name_plural = _('synchronized tables')

    def __str__(self):
        return self.table + ", " + str(self.alias) + " (" + str(self.id) + ")"

    def details(self, search=None, user=None):
        from ibartionmap.utils.functions import connect_with_on_map

        # if search:
        #     if not search.islower():
        #         search = search.lower()

        connection_on_map = connect_with_on_map()
        if self.is_virtual:
            fields = [field["alias"] for field in self.fields]
            cursor = connection_on_map.cursor(cursor_factory=RealDictCursor)
            sql = "SELECT {0} FROM {1}".format(", ".join(map(str, fields)), self.table)
            if search:
                sql += " WHERE "
                for index, field in enumerate(fields, start=1):
                    sql += " {0} LIKE '%{1}%' {2} ".format(field, search, "" if index == len(fields) else "OR")
                print(sql)
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
            except Exception as e:
                print(e.__str__())
                data = []
        else:
            fields = [field["Field"] for field in self.fields if field.get("selected") is True]
            connection_on_map = connect_with_on_map()
            cursor = connection_on_map.cursor(cursor_factory=RealDictCursor)
            sql = "SELECT {0} FROM {1}".format(", ".join(map(str, fields)), self.table)

            if search:
                sql += " WHERE "
                for index, field in enumerate(fields, start=1):
                    sql += " {0} LIKE '%{1}%' {2} ".format(field, search, "" if index == len(fields) else "OR")

            cursor.execute(sql)
            try:
                data = cursor.fetchall()
            except Exception as e:
                print(e.__str__())
                data = []

        connection_on_map.close()
        return data


class DataGroup(ModelBase):
    description = models.CharField(max_length=100, verbose_name=_('description'), unique=True)
    properties = models.JSONField(default=list)
    table = models.ForeignKey(
        SynchronizedTables,
        verbose_name=_('table'),
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.description + " (" + str(self.id) + ")"


class RelationsTable(ModelBase):
    table_one = models.ForeignKey(
        SynchronizedTables,
        related_name="table_one",
        verbose_name=_('table one'),
        on_delete=models.CASCADE,
    )
    table_two = models.ForeignKey(
        SynchronizedTables,
        related_name="table_two",
        verbose_name=_('table two'),
        on_delete=models.CASCADE,
    )
    property_table_one = models.CharField(max_length=100, verbose_name=_('property table one'))
    property_table_two = models.CharField(max_length=100, verbose_name=_('property table two'))

    def __str__(self):
        return self.table_one.table + " - " + self.table_two.table


class Marker(ModelBase):
    URL = 1
    FIELD = 2
    ICON_MAPS = 3

    TYPES_ICON = (
        (URL, _('Url')),
        (FIELD, _('Campo')),
        (ICON_MAPS, _('Icono Maps')),
    )
    name = models.CharField(max_length=250, verbose_name=_('name'), default='Marcador')
    table = models.ForeignKey(
        SynchronizedTables,
        verbose_name=_('table'),
        related_name=_('markers'),
        on_delete=models.CASCADE,
    )
    tables = models.ManyToManyField(
        SynchronizedTables,
        verbose_name=_('tables'),
        related_name=_('markers_list'),
    )
    field_latitude = models.JSONField(verbose_name=_('property latitude'), default=dict)
    field_longitude = models.JSONField(verbose_name=_('property longitude'), default=dict)
    group_by_field = models.JSONField(verbose_name=_('group by field'), default=dict)
    type_icon = models.SmallIntegerField(choices=TYPES_ICON, default=URL, verbose_name=_('type icon'))
    field_icon = models.JSONField(verbose_name=_('field icon'), default=dict)
    url_icon = models.TextField(verbose_name=_('url icon'), default=None, null=True)
    maps_icon = models.CharField(max_length=255, verbose_name=_('maps icon'), default=None, null=True)


def post_save_synchronized_table(sender, instance: SynchronizedTables, **kwargs):
    from ibartionmap.utils.functions import create_table_virtual
    if instance.is_virtual:
        create_table_virtual(instance)


def post_delete_synchronized_table(sender, instance: SynchronizedTables, **kwargs):
    connection_on_map = connect_with_on_map()
    try:
        cursor_on_map = connection_on_map.cursor()
        sql = "DROP TABLE IF EXISTS {0}".format(instance.table)
        cursor_on_map.execute(sql)
        connection_on_map.commit()
    except Exception:
        pass


post_save.connect(post_save_synchronized_table, sender=SynchronizedTables)

post_delete.connect(post_delete_synchronized_table, sender=SynchronizedTables)
