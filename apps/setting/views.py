from django.core.exceptions import ObjectDoesNotExist
from django_celery_beat.models import IntervalSchedule
from django_celery_results.models import TaskResult
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters import rest_framework as filters

from ibartionmap.utils.functions import connect_with_mysql, connect_with_on_map, get_tipo_mysql_to_pg, get_name_table
from .models import Connection
from .serializers import ConnectionDefaultSerializer, TaskResultDefaultSerializer, IntervalScheduleSerializer
from .tasks import sync_with_connection
from ..core.models import SynchronizedTables


class ConnectionFilter(filters.FilterSet):
    table = filters.CharFilter()

    class Meta:
        model = Connection
        fields = ['description', 'type', 'host', 'database_name', 'database_username', 'database_password',
                  'database_port', 'table']


class ConnectionViewSet(ModelViewSet):
    queryset = Connection.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ConnectionFilter
    serializer_class = ConnectionDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or None if pagination is disabled.
        """
        not_paginator = self.request.query_params.get('not_paginator', None)
        if self.paginator is None or not_paginator:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    @action(methods=['GET'], detail=False)
    def field_options(self, request):
        field = self.request.query_params.get('field', None)
        fields = self.request.query_params.getlist('fields', None)
        if fields:
            try:
                data = {}
                for field in fields:
                    data[field] = []
                    for c in Connection._meta.get_field(field).choices:
                        data[field].append({
                            "value": c[0],
                            "description": c[1]
                        })
                return Response(data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        elif field:
            try:
                choices = []
                for c in Connection._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=True)
    def sync_tables(self, request, pk):
        instance: Connection = self.get_object()
        try:
            result = []
            if instance.type == Connection.DB and instance.database_origin == Connection.MySQL:
                # Connect to the database
                connection = connect_with_mysql(instance)
                with connection:
                    with connection.cursor() as cursor:
                        # Read a single record
                        sql = "SHOW TABLES"
                        cursor.execute(sql)
                        tables = cursor.fetchall()

                    for t in list(tables):
                        table = t["Tables_in_" + instance.database_name]
                        with connection.cursor() as cursorTablas:
                            try:
                                # Read a single record
                                sql = "SHOW COLUMNS FROM " + table
                                cursorTablas.execute(sql)
                                fields = cursorTablas.fetchall()
                                result.append({
                                    "table": table,
                                    "fields": list(fields)
                                })
                            except Exception as e:
                                return Response({
                                    "table": table,
                                    "error": e.__str__()
                                }, status=status.HTTP_400_BAD_REQUEST)
                    sql = ""
                    fields_table = []
                try:
                    connection_on_map = connect_with_on_map()
                    cursor = connection_on_map.cursor()
                    for data in result:
                        table_name = get_name_table(instance, data['table'])
                        fields_table = []
                        for field in data["fields"]:
                            if field["Field"].startswith("MAX("):
                                break
                            char_null = "NOT NULL" if field["Null"] == "NO" else ""
                            char_type = get_tipo_mysql_to_pg(field["Type"])
                            fields_table.append(
                                "{0} {1} {2}".format(field["Field"], char_type, char_null)
                            )
                        sql = "DROP TABLE IF EXISTS {0}".format(table_name)
                        cursor.execute(sql)
                        connection_on_map.commit()
                        sql = "CREATE TABLE {0} ({1});".format(table_name, ", ".join(map(str, fields_table)))
                        cursor.execute(sql)
                        connection_on_map.commit()
                        try:
                            synchronized_table = SynchronizedTables.objects.get(
                                table=table_name, connection_id=instance.id
                            )
                            synchronized_table.fields = list(data["fields"])
                            synchronized_table.save(update_fields=['fields'])
                        except ObjectDoesNotExist:
                            SynchronizedTables.objects.create(
                                table_origin=data["table"],
                                table=table_name,
                                alias="",
                                fields=data["fields"],
                                is_virtual=False,
                                connection_id=instance.id
                            )
                    connection_on_map.close()
                except Exception as e:
                    return Response({
                        "sql": sql,
                        "fields_table": fields_table,
                        "error": e.__str__()
                    }, status=status.HTTP_400_BAD_REQUEST)
                instance.info_to_sync = result
                instance.save(update_fields=["info_to_sync"])
            # result = sync_with_connection(instance.id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(e.__str__(), status=status.HTTP_400_BAD_REQUEST)


class TaskResultViewSet(ModelViewSet):
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or None if pagination is disabled.
        """
        not_paginator = self.request.query_params.get('not_paginator', None)

        if not_paginator:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    @action(methods=['GET'], detail=False)
    def field_options(self, request):
        field = self.request.query_params.get('field', None)
        fields = self.request.query_params.getlist('fields', None)
        if fields:
            try:
                data = {}
                for field in fields:
                    data[field] = []
                    for c in TaskResult._meta.get_field(field).choices:
                        data[field].append({
                            "value": c[0],
                            "description": c[1]
                        })
                return Response(data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        elif field:
            try:
                choices = []
                for c in TaskResult._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)


class IntervalScheduleViewSet(ModelViewSet):
    queryset = IntervalSchedule.objects.all()
    serializer_class = IntervalScheduleSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []
    
    @action(methods=['GET'], detail=False)
    def field_options(self, request):
        field = self.request.query_params.get('field', None)
        fields = self.request.query_params.getlist('fields', None)
        if fields:
            try:
                data = {}
                for field in fields:
                    data[field] = []
                    for c in IntervalSchedule._meta.get_field(field).choices:
                        data[field].append({
                            "value": c[0],
                            "description": c[1]
                        })
                return Response(data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        elif field:
            try:
                choices = []
                for c in IntervalSchedule._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

