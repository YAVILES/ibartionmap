import json

from celery import shared_task

# Sincronización de tablas o recursos
from apps.core.models import SynchronizedTables
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
                for data in instance.info_to_sync_selected:
                    with connection.cursor() as cursor:
                        table = data["table"]
                        sql = "SELECT " + ", ".join(map(str, data["fields"])) + " FROM " + table
                        cursor.execute(sql)
                        results = cursor.fetchall()
                        SynchronizedTables.objects.update_or_create(
                            table=table,
                            defaults={
                                "data": json.loads(json.dumps(results, cls=PythonObjectEncoder))
                            },
                        )
    except ValueError as e:
        print(e.__str__())
