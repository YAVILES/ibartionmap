import json

from celery import shared_task

# Sincronización de tablas o recursos
from django.core.exceptions import ObjectDoesNotExist

from apps.core.models import SynchronizedTables, SynchronizedTablesData
from apps.setting.models import Connection
from ibartionmap.utils.functions import connect_with_mysql, PythonObjectEncoder


@shared_task(name="sync_with_connection")
def sync_with_connection(connection_id):
    try:
        instance: Connection = Connection.objects.get(id=connection_id)
        if instance.type == Connection.DB and instance.database_origin == Connection.MySQL:
            # Connect to the database
            connection = connect_with_mysql(instance)
            with connection:
                for table in instance.info_to_sync_selected:
                    fields = []
                    try:
                        synchronized_table = SynchronizedTables.objects.get(
                            table=table, connection_id=connection_id, is_virtual=False
                        )
                    except ObjectDoesNotExist:
                        for info in instance.info_to_sync:
                            if info.get('table') == table:
                                fields_table = info.get('fields')
                                for field in fields_table:
                                    field["selected"] = False
                                break
                        if fields_table is None:
                            break
                        else:
                            synchronized_table = SynchronizedTables.objects.create(
                                table=table,
                                alias="",
                                fields=fields_table,
                                show_on_map=False,
                                property_latitude=None,
                                property_longitude=None,
                                is_virtual=False,
                                connection=instance
                            )

                    for field in synchronized_table.fields:
                        if field["selected"]:
                            fields.append(field["Field"])
                    if fields:
                        with connection.cursor() as cursor:
                            sql = "SELECT " + ", ".join(map(str, fields)) + " FROM " + table
                            cursor.execute(sql)
                            results = cursor.fetchall()
                            items = []
                            for d in json.loads(json.dumps(results, cls=PythonObjectEncoder)):
                                items.append(
                                    SynchronizedTablesData(
                                        table_id=synchronized_table.id,
                                        data=d
                                    )
                                )
                            SynchronizedTablesData.objects.filter(table_id=synchronized_table.id).delete()
                            SynchronizedTablesData.objects.bulk_create(items)
    except ValueError as e:
        print(e.__str__())
