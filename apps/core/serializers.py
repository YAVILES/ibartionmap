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

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table', 'alias', 'fields')


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table = serializers.CharField(required=False)
    alias = serializers.CharField(required=False)
    data_groups = serializers.SerializerMethodField(read_only=True)

    def get_data_groups(self, table: SynchronizedTables):
        request = self.context.get('request')
        return DataGroupDefaultSerializer(DataGroup.objects.filter(table_id=table.id), many=True).data

    def validate(self, attrs):
        is_virtual = attrs.get('is_virtual')
        if is_virtual:
            relation: RelationsTable = attrs.get('tables', None)
            if relation is None:
                raise serializers.ValidationError(detail={
                    'error': "Debe identificar las tablas a utilizar"
                })
            alias = str(attrs.get('alias'))
            attrs['table'] = "{0}_{1}_{2}".format(
                relation.table_one.table, relation.table_two.table, alias.replace(" ", "").lower()
            )
            if SynchronizedTables.objects.filter(alias=attrs['alias']).exists():
                raise serializers.ValidationError(detail={
                    'error': "Ya existe una tabla con este nombre"
                })
        return attrs

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table_origin', 'table', 'alias', 'fields', 'connection_id', 'is_active', 'is_virtual',
                  'data_groups', 'details',)


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

    class Meta:
        model = RelationsTable
        fields = serializers.ALL_FIELDS

