import uuid
from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _

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


class ModelBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(verbose_name=_('created'), auto_now_add=True)
    updated = models.DateTimeField(verbose_name=_('updated'), auto_now=True)

    class Meta:
        abstract = True


class SynchronizedTables(ModelBase):
    table = models.CharField(max_length=100, verbose_name=_('table'), unique=True)
    alias = models.CharField(max_length=255, verbose_name=_('alias'))
    data = models.JSONField(default=list)
    show_on_map = models.BooleanField(default=False)
    property_longitude = models.CharField(max_length=255, verbose_name=_("property longitude"), blank=True, null=True)
    property_latitude = models.CharField(max_length=255, verbose_name=_("property latitude"), blank=True, null=True)

    class Meta:
        verbose_name = _('synchronized table')
        verbose_name_plural = _('synchronized tables')

    def __str__(self):
        return self.table + ", " + str(self.alias) + " (" + str(self.id) + ")"


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