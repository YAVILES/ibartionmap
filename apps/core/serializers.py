from django.core.exceptions import ObjectDoesNotExist
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from .models import SynchronizedTables, DataGroup, RelationsTable


class SynchronizedTablesDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    data = serializers.SerializerMethodField(read_only=True)

    def get_data(self, obj: SynchronizedTables):
        if obj.show_on_map:
            for d in obj.data:
                if d[obj.property_longitude] and d[obj.property_latitude]:
                    d["point"] = {
                        "longitude": d[obj.property_longitude],
                        "latitude": d[obj.property_latitude]
                    }
                else:
                    d["point"] = None
        return obj.data

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

    class Meta:
        model = RelationsTable
        fields = serializers.ALL_FIELDS

