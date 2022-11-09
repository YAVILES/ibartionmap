from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from ibartionmap.utils.functions import generate_virtual_sql
from .models import SynchronizedTables, DataGroup, RelationsTable, get_table_repeat_number, Marker


class SynchronizedTablesSimpleDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table = serializers.CharField(required=True)
    alias = serializers.CharField(required=False)

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table', 'alias', 'fields')


class RelationsCreateTableSerializer(serializers.ModelSerializer):
    table_one = serializers.UUIDField(required=True)
    table_two = serializers.UUIDField(required=True)
    property_table_one = serializers.CharField(max_length=100, required=True)
    property_table_two = serializers.CharField(max_length=100, required=True)

    class Meta:
        model = RelationsTable
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


class MarkerDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        required=True
    )
    tables = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        many=True,
        required=True
    )

    data_groups = serializers.SerializerMethodField(read_only=True)

    def get_data_groups(self, marker: Marker):
        request = self.context.get('request')
        return DataGroupDefaultSerializer(DataGroup.objects.filter(table__in=marker.tables.all()), many=True).data

    class Meta:
        model = Marker
        fields = serializers.ALL_FIELDS


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table_origin = serializers.CharField(required=False)
    table = serializers.CharField(required=False)
    alias = serializers.CharField(required=False)
    data_groups = serializers.SerializerMethodField(read_only=True)
    relations = serializers.PrimaryKeyRelatedField(
        queryset=RelationsTable.objects.all(),
        many=True,
        required=False
    )
    relations_table = RelationsCreateTableSerializer(many=True, required=False)
    markers = MarkerDefaultSerializer(many=True, read_only=True)

    def get_data_groups(self, table: SynchronizedTables):
        request = self.context.get('request')
        return DataGroupDefaultSerializer(DataGroup.objects.filter(table_id=table.id), many=True).data

    def validate(self, attrs):
        if attrs.get('is_virtual', False):
            if SynchronizedTables.objects.filter(alias=attrs['alias']).exists():
                raise serializers.ValidationError(detail={
                    'error': "Ya existe una tabla con este alias"
                })
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                validated_data['table'] = ""
                for table in validated_data.get('tables', []):
                    validated_data['table'] += "{0}".format(
                        table.table_origin
                    )

                try:
                    SynchronizedTables.objects.get(table=validated_data['table'])
                    validated_data['table'] += str(get_table_repeat_number(validated_data['table']))
                except ObjectDoesNotExist:
                    pass

                if validated_data.get('is_virtual', False):
                    validated_data['sql'] = generate_virtual_sql(validated_data)
                    relations = []
                    for relation in validated_data.pop('relations_table', []):
                        rel = RelationsTable.objects.create(
                            table_one_id=relation["table_one"],
                            table_two_id=relation["table_two"],
                            property_table_one=relation["property_table_one"],
                            property_table_two=relation["property_table_two"]
                        )
                        relations.append(rel.id)
                    validated_data['relations'] = relations
                synchronized_table = super(SynchronizedTablesDefaultSerializer, self).create(validated_data)
                return synchronized_table
        except ValidationError as error:
            raise serializers.ValidationError(detail={"error": error.messages})
        return validated_data

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                validated_data['table'] = ""
                for table in validated_data.get('tables', []):
                    validated_data['table'] += "{0}".format(
                        table.table_origin
                    )
                if validated_data.get('is_virtual', False):
                    validated_data['sql'] = generate_virtual_sql(validated_data)
                    relations = []
                    RelationsTable.objects.filter(id__in=[rel.id for rel in instance.relations]).delete()
                    for relation in validated_data.pop('relations_table', []):
                        rel = RelationsTable.objects.create(
                            table_one_id=relation["table_one"],
                            table_two_id=relation["table_two"],
                            property_table_one=relation["property_table_one"],
                            property_table_two=relation["property_table_two"]
                        )
                        relations.append(rel.id)
                    validated_data['relations'] = relations
                synchronized_table = super(SynchronizedTablesDefaultSerializer, self).update(instance, validated_data)
                return synchronized_table
        except ValidationError as error:
            raise serializers.ValidationError(detail={"error": error.messages})
        return instance

    class Meta:
        model = SynchronizedTables
        fields = ('id', 'table_origin', 'table', 'alias', 'fields', 'connection_id', 'is_active', 'is_virtual',
                  'data_groups', 'details', 'relations', 'relations_table', 'sql', 'tables', 'markers',)


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

