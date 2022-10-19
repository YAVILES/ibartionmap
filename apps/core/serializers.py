from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from .models import SynchronizedTables, DataGroup, RelationsTable, SynchronizedTablesData


class SynchronizedTableDataDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = SynchronizedTablesData
        fields = serializers.ALL_FIELDS


class SynchronizedTablesSimpleDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table = serializers.CharField(required=True)
    alias = serializers.CharField(required=False)
    full_fields = serializers.SerializerMethodField(read_only=True)

    def get_full_fields(self, table: SynchronizedTables):
        relations_table = RelationsTable.objects.filter(
            Q(table_one__id=table.id) | Q(Q(two_dimensional=True) & Q(table_two__id=table.id))
        )
        fields = table.fields
        keys = [field.get('Field') for field in fields if field.get('Field', None)]
        for relation in relations_table:
            if relation.table_two.id == table.id and relation.table_one.table not in keys:
                fields.append({'Field': relation.table_one.table, 'relation': relation.id})
            elif relation.table_two.table not in keys:
                fields.append({'Field': relation.table_two.table, 'relation': relation.id})
        return fields

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table', 'alias', 'full_fields', 'fields', 'show_on_map', 'property_latitude',
                  'property_longitude', 'property_icon',)


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    serialized_data = serializers.SerializerMethodField(read_only=True)
    table = serializers.CharField(required=False)
    alias = serializers.CharField(required=False)
    is_virtual = serializers.BooleanField(required=False, default=True)
    data_groups = serializers.SerializerMethodField(read_only=True)
    full_fields = serializers.SerializerMethodField(read_only=True)

    def get_full_fields(self, table: SynchronizedTables):
        relations_table = RelationsTable.objects.filter(
            Q(table_one__id=table.id) | Q(Q(two_dimensional=True) & Q(table_two__id=table.id))
        )
        fields = table.fields
        keys = [field.get('Field') for field in fields if field.get('Field', None)]
        for relation in relations_table:
            if relation.table_two.id == table.id and relation.table_one.table not in keys:
                fields.append({'Field': relation.table_one.table, 'relation': relation.id})
            elif relation.table_two.table not in keys:
                fields.append({'Field': relation.table_two.table, 'relation': relation.id})
        return fields

    def get_serialized_data(self, table: SynchronizedTables):
        request = self.context.get('request')
        return table.serialized_data(request.query_params.get('search', None), request.user)

    def get_data_groups(self, table: SynchronizedTables):
        request = self.context.get('request')
        return DataGroupDefaultSerializer(DataGroup.objects.filter(table_id=table.id), many=True).data

    def validate(self, attrs):
        is_virtual = attrs.get('is_virtual')
        if is_virtual:
            relation: RelationsTable = attrs.get('relation', None)
            if relation is None:
                raise serializers.ValidationError(detail={
                    'error': "Debe identificar la relacion obligatoriamente en las tablas virtuales"
                })
            alias = str(attrs.get('alias'))
            attrs['table'] = "{0}_{1}_{2}".format(
                relation.table_one.table, relation.table_two.table, alias.replace(" ", "").lower()
            )
            if SynchronizedTables.objects.filter(table=attrs['table']).exists():
                raise serializers.ValidationError(detail={
                    'error': "Ya existe una tabla con este nombre"
                })
        return attrs

    class Meta:
        model = SynchronizedTables
        fields = serializers.ALL_FIELDS


class DataGroupDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    properties = serializers.ListField(required=True)
    table = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        required=True
    )

    def validate(self, attrs):
        error_properties = []
        properties: list = attrs.get("properties")
        table: SynchronizedTables = attrs.get("table")
        for _property in properties:
            try:
                data_group = DataGroup.objects.get(properties__contains=_property, table_id=table.id)
                if data_group:
                    error_properties.append(
                        {
                            "property": _property,
                            "data_group": DataGroupDefaultSerializer(data_group).data
                        }
                    )
            except ObjectDoesNotExist:
                pass

        if error_properties:
            raise serializers.ValidationError(detail={
                'error': _("Some selected properties already exist in another data group for this table"),
                'data': error_properties
            })
        else:
            return attrs

    class Meta:
        model = DataGroup
        fields = serializers.ALL_FIELDS


class RelationsTableDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table_one = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        required=True
    )
    table_two = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        required=True
    )
    table_one_display = SynchronizedTablesSimpleDefaultSerializer(read_only=True, source="table_one")
    table_two_display = SynchronizedTablesSimpleDefaultSerializer(read_only=True, source="table_two")
    property_table_one = serializers.CharField(max_length=100, required=True)
    property_table_two = serializers.CharField(max_length=100, required=True)
    two_dimensional = serializers.BooleanField(default=False)

    '''
    def validate(self, attrs):
        table_one: SynchronizedTables = attrs.get("table_one")
        table_two: SynchronizedTables = attrs.get("table_two")
        try:
            relations_table = RelationsTable.objects.get(
                Q(Q(table_one_id=table_one.id) & Q(table_two_id=table_two.id)) |
                Q(Q(table_one_id=table_two.id) & Q(table_two_id=table_one.id))
            )
            raise serializers.ValidationError(detail={
                'error': _("There is already a relationship between these tables"),
                'relation': RelationsTableDefaultSerializer(relations_table).data
            })
        except ObjectDoesNotExist:
            pass
        return attrs
    '''

    class Meta:
        model = RelationsTable
        fields = serializers.ALL_FIELDS

