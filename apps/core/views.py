from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from psycopg2.extras import RealDictCursor
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters import rest_framework as filters

from ibartionmap.utils.functions import connect_with_on_map, generate_virtual_sql, create_table_virtual
from .models import SynchronizedTables, DataGroup, RelationsTable, Marker
from .serializers import SynchronizedTablesDefaultSerializer, DataGroupDefaultSerializer, \
    RelationsTableDefaultSerializer, SynchronizedTablesSimpleDefaultSerializer, MarkerDefaultSerializer
from ..setting.models import Connection


class SynchronizedTablesFilter(filters.FilterSet):
    class Meta:
        model = SynchronizedTables
        fields = ['table', 'alias', 'is_active', 'connection_id', 'is_virtual']


class SynchronizedTablesViewSet(ModelViewSet):
    queryset = SynchronizedTables.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = SynchronizedTablesFilter
    serializer_class = SynchronizedTablesDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []
    search_fields = []

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if not user.is_anonymous:
            if user.is_superuser:
                return queryset
            else:
                return queryset.filter(id__in=user.data_groups.all().values_list('table__id', flat=True))

        return queryset

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
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
                    for c in SynchronizedTables._meta.get_field(field).choices:
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
                for c in SynchronizedTables._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False)
    def get_table(self, request):
        connection = self.request.query_params.get('connection', None)
        table = self.request.query_params.get('table', None)
        if connection and table:
            try:
                connection = Connection.objects.get(pk=connection)
                fields = None
            except ObjectDoesNotExist:
                return Response(
                    {"error": "La conexión no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                synchronized_table = SynchronizedTables.objects.get(
                    Q(
                        Q(connection_id=connection) | Q(is_virtual=True)
                    ) & Q(table=table)
                )
                return Response(
                    SynchronizedTablesSimpleDefaultSerializer(synchronized_table).data,
                    status=status.HTTP_200_OK
                )
            except ObjectDoesNotExist:
                for info in connection.info_to_sync:
                    if info.get('table') == table:
                        fields = info.get('fields')
                        break
                if fields is None:
                    return Response(
                        {"error": "La tabla no existe"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                synchronized_table = SynchronizedTables.objects.create(
                    table=table,
                    alias="",
                    fields=fields,
                    property_latitude=None,
                    property_longitude=None,
                    is_virtual=False,
                    connection=connection
                )
                return Response(
                    SynchronizedTablesSimpleDefaultSerializer(synchronized_table).data,
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {"error": "Debes enviar el id de la conexion y el nombre de la tabla"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['POST'], detail=False)
    def virtual_preview(self, request):
        data = request.data
        table_data = SynchronizedTablesDefaultSerializer(
            SynchronizedTables(
                alias="",
                fields=data["fields"],
                is_virtual=True
            ),
            exclude=['details', 'sql']
        ).data
        result = []
        sql = generate_virtual_sql(data)
        if sql:
            try:
                connection_on_map = connect_with_on_map()
                cursor = connection_on_map.cursor(cursor_factory=RealDictCursor)
                cursor.execute(sql)
                result = cursor.fetchall()
                connection_on_map.close()
            except Exception as e:
                connection_on_map.close()
                return Response(
                    {
                        "sql": sql,
                        "error": e.__str__()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        table_data["details"] = result
        table_data["sql"] = sql
        return Response(
            table_data,
            status=status.HTTP_200_OK
        )

    @action(methods=['POST'], detail=True)
    def test_create(self, request, pk):
        instance: SynchronizedTables = self.get_object()
        try:
            result = create_table_virtual(instance)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(e.__str__(), status=status.HTTP_400_BAD_REQUEST)


class DataGroupFilter(filters.FilterSet):
    class Meta:
        model = DataGroup
        fields = ['description', 'table']


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DataGroupFilter
    serializer_class = DataGroupDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
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
                    for c in DataGroup._meta.get_field(field).choices:
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
                for c in DataGroup._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)


class RelationsTableFilter(filters.FilterSet):
    class Meta:
        model = RelationsTable
        fields = ['table_one', 'table_two', 'property_table_one', 'property_table_two', 'table_one__connection_id']


class RelationsTableViewSet(ModelViewSet):
    queryset = RelationsTable.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RelationsTableFilter
    serializer_class = RelationsTableDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
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
                    for c in RelationsTable._meta.get_field(field).choices:
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
                for c in RelationsTable._meta.get_field(field).choices:
                    choices.append({
                        "value": c[0],
                        "description": c[1]
                    })
                return Response(choices, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "the field parameter is mandatory"}, status=status.HTTP_400_BAD_REQUEST)


class MarkerFilter(filters.FilterSet):
    class Meta:
        model = Marker
        fields = ['table_id']


class MarkerViewSet(ModelViewSet):
    queryset = Marker.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = MarkerFilter
    serializer_class = MarkerDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        not_paginator = self.request.query_params.get('not_paginator', None)
        if self.paginator is None or not_paginator:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)