import uuid
import json

from django.db.models import CharField
from django.db.models.functions import Cast, Lower
from django.db.models.query_utils import Q
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from bulk_update_or_create import BulkUpdateOrCreateQuerySet

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


def map_virtual(id, data, fields, show_on_map, table_geo_id, property_latitude, property_longitude, property_icon):
    d = {}
    for field in fields:
        if field in data.keys():
            d[field] = data[field]
    obj = {}
    if show_on_map:
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
            for data_group in DataGroup.objects.filter(table_id=id):
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


class SynchronizedTables(ModelBase):
    table = models.CharField(max_length=100, verbose_name=_('table'), unique=True)
    alias = models.CharField(max_length=255, verbose_name=_('alias'))
    fields = models.JSONField(default=list)
    show_on_map = models.BooleanField(default=False)
    table_geo = models.ForeignKey(
        'core.SynchronizedTables',
        verbose_name=_('table geo'),
        on_delete=models.CASCADE,
        null=True
    )
    property_latitude = models.CharField(max_length=255, verbose_name=_("property latitude"), blank=True, null=True)
    property_longitude = models.CharField(max_length=255, verbose_name=_("property longitude"), blank=True, null=True)
    property_icon = models.TextField(verbose_name=_("property icon url"), blank=True, null=True)
    connection = models.ForeignKey(
        'setting.Connection',
        verbose_name=_('connection'),
        on_delete=models.CASCADE,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_virtual = models.BooleanField(default=False)
    relation = models.ForeignKey(
        'core.RelationsTable',
        verbose_name=_('relation'),
        on_delete=models.CASCADE,
        null=True,
        default=None
    )

    class Meta:
        verbose_name = _('synchronized table')
        verbose_name_plural = _('synchronized tables')

    def __str__(self):
        return self.table + ", " + str(self.alias) + " (" + str(self.id) + ")"

    @cached_property
    def details(self):
        search = self.request.query_params.get('search', None)
        if search is None:
            return self.data.all()
        else:
            if not search.islower():
                search = search.lower()
            return self.data.all().annotate(
                data_format=Lower(Cast('data', output_field=CharField())),
            ).filter(
                data_format__contains=search
            )

    def serialized_data(self, search=None, user=None):
        if self.is_virtual:
            fields = list(set([
                (field.get('table'), field.get('Field')) for field in self.fields
                if not field.get('table', None) is None and not field.get('Field') is None
            ]))
            relation: RelationsTable = self.relation
            serialized_data = []
            if search:
                if not search.islower():
                    search = search.lower()
                data_one = relation.table_one.data.all().annotate(
                    info_format=Lower(Cast('data', output_field=CharField()))
                ).filter(info_format__contains=search).values_list('data', flat=True)
                data_two = relation.table_two.data.all().annotate(
                    info_format=Lower(Cast('data', output_field=CharField()))
                ).filter(info_format__contains=search).values_list('data', flat=True)
            else:
                data_one = relation.table_one.data.all().values_list('data', flat=True)
                data_two = relation.table_two.data.all().values_list('data', flat=True)

            for d_one in data_one:
                keys_d_one = list(d_one.keys())
                for d_two in data_two:
                    if relation.property_table_one in keys_d_one and \
                            d_one[relation.property_table_one] == d_two[relation.property_table_two]:
                        if self.table_geo.id == relation.table_one.id:
                            d_one['table'] = str(relation.table_one.id)
                        else:
                            d_one['table'] = str(relation.table_two.id)
                        keys_d_two = list(d_two.keys())
                        for key in keys_d_one:
                            if key in keys_d_two:
                                if self.table_geo.id == relation.table_one.id:
                                    d_two[key+"1"] = d_two[key]
                                    d_two.pop(key)
                                else:
                                    d_one[key + "1"] = d_one[key]
                                    d_one.pop(key)
                        d_one.update(d_two)
                        serialized_data.append(d_one)
                        break
            f = [field[1] for field in fields]
            return map(
                lambda e: map_virtual(
                    self.id, e, f, self.show_on_map, str(self.table_geo.id), self.property_latitude,
                    self.property_longitude, self.property_icon
                ),
                serialized_data
            )
        else:
            if search:
                if not search.islower():
                    search = search.lower()
                data = self.data.all().annotate(
                    info_format=Lower(Cast('data', output_field=CharField()))
                ).filter(info_format__contains=search).values_list('data', flat=True)
            else:
                data = self.data.all().values_list('data', flat=True)
            relations_table = RelationsTable.objects.filter(
                Q(table_one__id=self.id) | Q(Q(two_dimensional=True) & Q(table_two__id=self.id))
            )
            serialized_data = []
            for d in data:
                obj = {}
                if self.show_on_map:
                    if self.property_icon:
                        obj[self.property_icon] = d[self.property_icon]

                    if d[self.property_longitude] and d[self.property_latitude]:
                        obj["point"] = {
                            "longitude": float(d[self.property_longitude]),
                            "latitude": float(d[self.property_latitude])
                        }
                    else:
                        obj["point"] = None

                    # if user:
                    #     if user.is_superuser:
                    for data_group in DataGroup.objects.filter(table_id=self.id):
                        for field in data_group.properties:
                            property_field = field.get('Field')
                            if property_field:
                                obj[property_field] = d[property_field]

                for relation in relations_table:
                    if relation.table_two.id == self.id:
                        data = [
                            d_one for d_one in relation.table_one.data.all().values_list('data', flat=True)
                            if d[relation.property_table_two] == d_one[relation.property_table_one]
                        ]
                        obj[relation.table_one.table] = data
                    else:
                        obj[relation.table_two.table] = [
                            d_two for d_two in relation.table_two.data.all().values_list('data', flat=True)
                            if d[relation.property_table_one] == d_two[relation.property_table_two]
                        ]
                serialized_data.append(obj)
        return serialized_data


class SynchronizedTablesData(ModelBase):
    table = models.ForeignKey(
        SynchronizedTables,
        verbose_name=_('table'),
        related_name=_('data'),
        on_delete=models.CASCADE
    )
    data = models.JSONField(default=dict)
    objects = BulkUpdateOrCreateQuerySet.as_manager()


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
    two_dimensional = models.BooleanField(default=False)

    def __str__(self):
        return self.table_one.table + " - " + self.table_two.table
