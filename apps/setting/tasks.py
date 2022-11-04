import json

from celery import shared_task

# Sincronización de tablas o recursos
from django.core.exceptions import ObjectDoesNotExist

from apps.core.models import SynchronizedTables
from apps.setting.models import Connection
from ibartionmap.utils.functions import connect_with_mysql, PythonObjectEncoder, get_name_table, connect_with_on_map, \
    formatter_field


@shared_task(name="sync_with_connection")
def sync_with_connection(connection_id):
    try:
        instance: Connection = Connection.objects.get(id=connection_id)
        if instance.type == Connection.DB and instance.database_origin == Connection.MySQL:
            # Connect to the database
            connection = connect_with_mysql(instance)
            connection_on_map = connect_with_on_map()
            with connection:
                for table_origin in instance.info_to_sync_selected:
                    for info in instance.info_to_sync:
                        if info.get('table') == get_name_table(instance, table_origin):
                            fields_table = info.get('fields')
                            for field in fields_table:
                                field["selected"] = False
                            break
                    if fields_table is None:
                        break
                    try:
                        synchronized_table = SynchronizedTables.objects.get(
                            table_origin=table_origin, connection_id=connection_id, is_virtual=False
                        )
                    except ObjectDoesNotExist:
                        synchronized_table = SynchronizedTables.objects.create(
                            table_origin=table_origin,
                            table=get_name_table(instance, table_origin),
                            alias="",
                            fields=fields_table,
                            is_virtual=False,
                            connection=instance
                        )

                    fields = [field["Field"] for field in fields_table]
                    if fields:
                        with connection.cursor() as cursor:
                            sql = "SELECT " + ", ".join(map(str, fields)) + " FROM " + table_origin
                            cursor.execute(sql)
                            results = cursor.fetchall()
                            data = json.loads(json.dumps(results, cls=PythonObjectEncoder))
                            try:
                                cursor_on_map = connection_on_map.cursor()
                                sql = "INSERT INTO {0} ({1}) VALUES".format(
                                    get_name_table(instance, table_origin),
                                    ", ".join(map(str, data[0].keys()))
                                )
                                records = [" ({0})".format(", ".join(map(formatter_field, d.values()))) for d in data]
                                sql += ", ".join(map(str, records))
                                cursor_on_map.execute(sql)
                                connection_on_map.commit()
                            except Exception as e:
                                return {
                                    "sql": sql,
                                    "fields_table": fields_table,
                                    "error": e.__str__()
                                }
            connection_on_map.close()
    except ValueError as e:
        print(e.__str__())
