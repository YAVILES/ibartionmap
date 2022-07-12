from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters import rest_framework as filters

from .models import SynchronizedTables, DataGroup, RelationsTable
from .serializers import SynchronizedTablesDefaultSerializer, DataGroupDefaultSerializer, \
    RelationsTableDefaultSerializer, SynchronizedTablesSimpleDefaultSerializer
from ..setting.models import Connection


class SynchronizedTablesFilter(filters.FilterSet):
    class Meta:
        model = SynchronizedTables
        fields = ['table', 'alias', 'show_on_map', 'is_active']


class SynchronizedTablesViewSet(ModelViewSet):
    queryset = SynchronizedTables.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = SynchronizedTablesFilter
    serializer_class = SynchronizedTablesDefaultSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

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
                synchronized_table = SynchronizedTables.objects.get(connection_id=connection, table=table)
                return Response(
                    SynchronizedTablesSimpleDefaultSerializer(synchronized_table).data,
                    status=status.HTTP_200_OK
                )
            except ObjectDoesNotExist:
                for info in connection.info_to_sync:
                    if info.get('table') == table:
                        fields = info.get('fields')
                        for field in fields:
                            field["selected"] = False
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
                    data=[],
                    show_on_map=False,
                    property_latitude=None,
                    property_longitude=None,
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
