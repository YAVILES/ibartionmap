from django_celery_results.models import TaskResult
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers

from apps.setting.models import Connection


class InfoToSyncSerializer(serializers.Serializer):
    table = serializers.CharField(required=True)
    fields = serializers.ListField(required=True)


class ConnectionDefaultSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    info_to_sync = InfoToSyncSerializer(many=True, required=False)
    info_to_sync_selected = InfoToSyncSerializer(many=True, required=False)

    class Meta:
        model = Connection
        fields = serializers.ALL_FIELDS


class TaskResultDefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskResult
        fields = serializers.ALL_FIELDS


