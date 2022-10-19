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
                        if field.get("selected") and field.get("relation") is None:
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

                for synchronized_table in SynchronizedTables.objects.filter(
                        is_virtual=True,
                        relation__table_one__connection_id=connection_id,
                        relation__table_two__connection_id=connection_id
                ):
                    if synchronized_table.fields:
                        fields = list(set([
                            (field.get('table'), field.get('Field')) for field in synchronized_table.fields
                            if not field.get('table', None) is None and not field.get('Field') is None
                        ]))
                        data = []
                        relation = synchronized_table.relation
                        data_one = relation.table_one.data.all().values_list('data', flat=True)
                        data_two = relation.table_two.data.all().values_list('data', flat=True)
                        for d_one in data_one:
                            keys_d_one = list(d_one.keys())
                            for d_two in data_two:
                                try:
                                    if d_one[relation.property_table_one] == d_two[relation.property_table_two]:
                                        if synchronized_table.table_geo.id == relation.table_one.id:
                                            d_one['table'] = str(relation.table_one.id)
                                        else:
                                            d_one['table'] = str(relation.table_two.id)
                                        keys_d_two = list(d_two.keys())
                                        for key in keys_d_one:
                                            if key in keys_d_two:
                                                if synchronized_table.table_geo.id == relation.table_one.id:
                                                    d_two[key + "1"] = d_two[key]
                                                    d_two.pop(key)
                                                else:
                                                    d_one[key + "1"] = d_one[key]
                                                    d_one.pop(key)
                                        d_one.update(d_two)
                                        data.append(d_one)
                                        break
                                except KeyError:
                                    pass
                        for d in json.loads(json.dumps(data, cls=PythonObjectEncoder)):
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
