from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers

from ibartionmap.utils.functions import generate_virtual_sql
from .models import SynchronizedTables, RelationsTable, get_table_repeat_number, Marker


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
        required=False
    )

    class Meta:
        model = Marker
        fields = serializers.ALL_FIELDS


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    table_origin = serializers.CharField(required=False)
    table = serializers.CharField(required=False)
    alias = serializers.CharField(required=False)
    relations = serializers.PrimaryKeyRelatedField(
        queryset=RelationsTable.objects.all(),
        many=True,
        required=False
    )
    relations_display = RelationsTableDefaultSerializer(
        many=True,
        read_only=True,
        source="relations"
    )
    relations_table = RelationsCreateTableSerializer(many=True, required=False)
    markers = MarkerDefaultSerializer(many=True, read_only=True)
    details = serializers.SerializerMethodField(read_only=True)
    tables = serializers.PrimaryKeyRelatedField(
        queryset=SynchronizedTables.objects.all(),
        many=True,
        required=False
    )

    def get_details(self, table: SynchronizedTables):
        request = self.context.get('request')
        return table.details(request.query_params.get('search', None), request.user)

    def validate(self, attrs):
        if attrs.get('is_virtual', False) and attrs.get('alias', False):
            if SynchronizedTables.objects.filter(alias=attrs['alias']).exists():
                raise serializers.ValidationError(detail={
                    'error': "Ya existe una tabla con este alias"
                })

        fields = attrs.get('fields', [])
        if not fields:
            raise serializers.ValidationError(detail={
                'error': "Debe seleccionar al menos un campo"
            })
        if attrs.get('is_virtual', False):
            fields_set = set()
            fields_duplicates = [x for x in fields if x.get('alias') in list(fields_set) or (fields_set.add(x.get('alias')) or False)]
            # print(fields_duplicates)
            if fields_duplicates:
                raise serializers.ValidationError(detail={
                    'error': "Existen nombres de campos duplicados",
                    'fields_duplicates': fields_duplicates
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
                if validated_data.get('is_virtual', None) and validated_data.get('relations_table', None):
                    validated_data['sql'] = generate_virtual_sql(validated_data)
                    relations = []
                    RelationsTable.objects.filter(id__in=[rel.id for rel in instance.relations.all()]).delete()
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
        fields = ('id', 'table_origin', 'table', 'alias', 'fields', 'connection_id', 'is_active', 'is_virtual', 'sql',
                  'details', 'relations', 'relations_table', 'relations_display', 'tables', 'markers',)
