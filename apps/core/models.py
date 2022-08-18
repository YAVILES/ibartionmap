import uuid
import json

from django.db.models.query_utils import Q
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

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


def map_virtual(data, fields):
    d = {}
    for field in fields:
        if field in data.keys():
            d[field] = data[field]
    return d


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
    data = models.JSONField(default=list)
    show_on_map = models.BooleanField(default=False)
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
    def serialized_data(self, user: 'security.User' = None):
        if self.is_virtual:
            self.data = []
            fields = list(set([
                (field.get('table'), field.get('Field')) for field in self.fields
                if not field.get('table', None) is None and not field.get('Field') is None
            ]))
            relation: RelationsTable = self.relation
            self.serialized_data = []
            for d_one in relation.table_one.data:
                for d_two in relation.table_two.data:
                    if d_one[relation.property_table_one] == d_two[relation.property_table_two]:
                        d_one.update(d_two)
                        self.serialized_data.append(d_one)
                        break
            f = [field[1] for field in fields]
            return map(lambda e: map_virtual(e, f), self.serialized_data)
        else:
            relations_table = RelationsTable.objects.filter(
                Q(table_one__id=self.id) | Q(Q(two_dimensional=True) & Q(table_two__id=self.id))
            )
            for d in self.data:
                if self.show_on_map:
                    if d[self.property_longitude] and d[self.property_latitude]:
                        d["point"] = {
                            "longitude": float(d[self.property_longitude]),
                            "latitude": float(d[self.property_latitude])
                        }
                    else:
                        d["point"] = None
                for relation in relations_table:
                    if relation.table_two.id == self.id:
                        data = [
                            d_one for d_one in relation.table_one.data
                            if d[relation.property_table_two] == d_one[relation.property_table_one]
                        ]
                        d[relation.table_one.table] = data
                    else:
                        d[relation.table_two.table] = [
                            d_two for d_two in relation.table_two.data
                            if d[relation.property_table_one] == d_two[relation.property_table_two]
                        ]
        return self.data


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
