from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from .models import SynchronizedTables, DataGroup, RelationsTable


class SynchronizedTablesSimpleDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table = serializers.CharField(required=True)
    alias = serializers.CharField(required=False)

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table', 'alias', 'fields', 'show_on_map', 'property_latitude', 'property_longitude',
                  'property_icon',)


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    serialized_data = serializers.ListField(read_only=True)
    table = serializers.CharField(required=False)
    alias = serializers.CharField(required=False)
    is_virtual = serializers.BooleanField(required=False, default=True)

    def create(self, validated_data):
        try:
            is_virtual = validated_data.get('is_virtual')
            if is_virtual:
                relation: RelationsTable = validated_data.get('relation', None)
                if relation is None:
                    raise serializers.ValidationError(detail={
                        'error': "Debe identificar la relacion obligatoriamente en las tablas virtuales"
                    })
                validated_data['table'] = "{0} {1}".format(relation.table_one.table, relation.table_two.table,)
            table = super(SynchronizedTablesDefaultSerializer, self).create(validated_data)
            return table
        except ValidationError as error:
            raise serializers.ValidationError(detail={"error": error.messages})

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

