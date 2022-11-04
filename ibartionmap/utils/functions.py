import datetime
from decimal import Decimal
from json import JSONEncoder
from uuid import UUID

import psycopg2
import pymysql.cursors
from constance import config
from constance.backends.database.models import Constance
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from apps.setting.models import Connection
from ibartionmap import settings
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True),
    MEDIA_URL=(str, 'http://localhost:8000/media'),
    SECRET_KEY=(str, '4)!6(7cj4wfibai#r%qk=o51ba-(^c-cevex_5e-3hr@4a8kr1'),
    DATABASE=(str, 'btpb2b'),
    DATABASE_USER=(str, 'postgres'),
    DATABASE_PASSWORD=(str, 'postgres'),
    DATABASE_HOST=(str, 'localhost'),
    DATABASE_PORT=(int, 5432),
    TIME_ZONE=(str, 'America/Caracas'),
    EMAIL_PASSWORD=(str, 'passEmail'),
    EMAIL_HOST_USER=(str, "example@gmail.com"),
    EMAIL_HOST=(str, 'smtp.googlemail.com'),
    EMAIL_PORT=(int, 587),
    PREFIX_APP=(str, 'dev'),
)

# reading .env file
environ.Env.read_env()


class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, QuerySet):
            try:
                data = dict(obj)
            except ValueError:
                data = list(obj)
            return data
        else:
            return JSONEncoder.default(self, obj)


def get_settings(allow_settings):
    setting_list = []
    for key, options in getattr(settings, 'CONSTANCE_CONFIG', {}).items():
        if key in allow_settings and key not in []:
            default, help_text = options[0], options[1]
            try:
                item = Constance.objects.get(key=key)
                value = item.value
                id = item.id
            except ObjectDoesNotExist:
                id = None
                value = getattr(config, key)
            data = {
                'id': id,
                'key': key,
                'default': default,
                'help_text': help_text,
                'value': value}
            setting_list.append(data)
    return setting_list


def format_headers_import(headers, add_info=None):
    for index, header in enumerate(headers):
        if headers in ["validodesde", "ValidoDesde"]:
            headers[index] = "valid_from"
        if headers in ["validohasta", "ValidoHasta"]:
            headers[index] = "valid_until"
        if headers in ["tasa", "Tasa"]:
            headers[index] = "rate"
        if header in ["Estado", "estado"]:
            headers[index] = "location_parent"
        if header in ["Ciudad", "ciudad"]:
            headers[index] = "location"
        if header in ["Father", "Padre", "Parent", "parent", "Categoria1", "CodCategoria"]:
            headers[index] = "parent"
        if header in ["CodUnidadMedida", "Abreviatura", "Categoria3"]:
            headers[index] = "abbreviation"
        if header in ["CodCliente", "CodClienteERP"]:
            headers[index] = "code_client"
        if header in ["Correo", "Email"]:
            headers[index] = "email"
        if header in ["Nombre", "Nombre1"]:
            headers[index] = "name"
        if header in ["Direccion", "Direccion1"]:
            headers[index] = "address"
        if header in ["Telefono1", "Telefono"]:
            headers[index] = "phone1"
        if header in ["Telefono2"]:
            headers[index] = "phone2"
        if header in ["NumeroTributario1", "NumeroTributario"]:
            headers[index] = "tax_number"
        if header in ["FechaStatus"]:
            headers[index] = "activation_date"
        if header in ["Status", "Estatus"]:
            headers[index] = "status"
        if header in ["LimiteCredito"]:
            headers[index] = "credit_limit_value"
        if header in ["CodTipoAccion", "TipoAccion"]:
            headers[index] = "type_action"
        if header in ["Saldo"]:
            headers[index] = "balance"
        if header in ["DiasCredito"]:
            headers[index] = "credit_days"
        if header in ["Nombreropietario"]:
            headers[index] = "owner_name"
        if header in ["FormaPago"]:
            headers[index] = "way_to_pay"
        if header in ["RazonSocial"]:
            headers[index] = "business_name"
        if header in ["CodTipoNegocio", "TipoNegocio"]:
            headers[index] = "business_type_code"
        if header in ["CodListaPrecioERP", "CodListaPrecio", "ListaPrecioERP", "ListaPrecio"]:
            headers[index] = "price_list"
        if header in ["Precio", "Precio1", "PrecioVenta"]:
            headers[index] = "price"
        if header in ["CODATRIBUTOCTE1"]:
            headers[index] = "code_attribute_cte1"
        if header in ["CODATRIBUTOCTE2"]:
            headers[index] = "code_attribute_cte2"
        if header in ["CODATRIBUTOCTE3"]:
            headers[index] = "code_attribute_cte3"
        if header in ["Codigo", "CodProducto", "CodClasificacion1", "CodClasificacion", "CodBanco"]:
            headers[index] = "code"
        if header in ["CodClasificacion1", "CodClasificacion"]:
            headers[index] = "internal_code"
        if header in ["DescripcionCorta", "Descripcion"]:
            headers[index] = "description"
        if header in ["AplicaIVA"]:
            headers[index] = "apply_iva"
        if header in ["TipoProducto"]:
            headers[index] = "product_type"
        if header in ["Unidades"]:
            headers[index] = "units"
        if header in ["Volumen"]:
            headers[index] = "volume"
        if header in ["Peso"]:
            headers[index] = "weight"
        if header in ["Categoria1", "Categoria"]:
            headers[index] = "category"
        if header in ["Categoria2", "SubCategoria"]:
            headers[index] = "subcategory"
        if header in ["EsVacio"]:
            headers[index] = "empty"
        if header in ["CodProductoVacio"]:
            headers[index] = "empty_product_code"
        if header in ["CantidadVacio"]:
            headers[index] = "quantity_empty"
        if header in ["Cantidad"]:
            headers[index] = "quantity"
        if header in ["PorcentajeIEPS"]:
            headers[index] = "IEPS_percentage"
        if header in ["UnidadDeAlmacenamiento"]:
            headers[index] = "storage_unit"
        if header in ["Foto", "Imagen"]:
            headers[index] = "imagen"
        if header in ["Marca"]:
            headers[index] = "brand"
        if header in ["Almacen", "Almacén", "Almacen1"]:
            headers[index] = "warehouse"
        if header in ["Moneda", "Coin"]:
            headers[index] = "coin"
        if header in ["CodExterno"]:
            headers[index] = "external_code"
        if header in ["CodAlmacen"]:
            headers[index] = "code_warehouse"
        if header in ["Pickup"]:
            headers[index] = "pickup"
        if header in ["CodAlmacen"]:
            headers[index] = "code_warehouse"
        if header in ["CodExterno"]:
            headers[index] = "external_code"
        if header in ["Alias"]:
            headers[index] = "alias"
        if header in ["Responsable"]:
            headers[index] = "responsible"
        if header in ["TipoDocumento"]:
            headers[index] = "document_type"
        if header in ["Cancelado"]:
            headers[index] = "canceled"
        if header in ["FechaEmision"]:
            headers[index] = "date_of_issue"
        if header in ["FechadeVencimiento"]:
            headers[index] = "due_date"
        if header in ["Total"]:
            headers[index] = "total"
        if header in ["Anulado"]:
            headers[index] = "annulled"
        if header in ["CodDocumentoERP"]:
            headers[index] = "document_code"

    return headers


def connect_with_mysql(instance: Connection):
    connection = pymysql.connect(
        host=instance.host,
        user=instance.database_username,
        password=instance.database_password,
        database=instance.database_name,
        port=instance.database_port,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def get_tipo_mysql_to_pg(typeField):
    """
        # Definir el tipo de dato de mysql a posgresql
        :param typeField:
        :return: str
    """
    if typeField.startswith("int") or typeField.startswith("tinyint"):
        return "integer"
    elif typeField.startswith("bigint"):
        return "bigint"
    elif typeField.startswith("datetime") or typeField.startswith("date"):
        return "varchar(30)"
        # return "timestamp without time zone"
    elif typeField.startswith("float") or typeField.startswith("double"):
        return "double precision"
    elif typeField.startswith("varbinary"):
        if typeField == "varbinary(0)":
            return "bit"
        return typeField.replace("varbinary", "bit")
    elif typeField.startswith("binary"):
        if typeField == "binary(0)":
            return "bit"
        return typeField.replace("binary", "bit")
    else:
        return typeField


def connect_with_on_map():
    connection = psycopg2.connect(
        host=env('DATABASE_HOST'),
        user=env('DATABASE_USER'),
        password=env('DATABASE_PASSWORD'),
        database=env('DATABASE'),
        port=env('DATABASE_PORT')
    )
    return connection


def get_name_table(connection, table_name):
    return "{0}_{1}".format(connection.database_name, table_name)


def formatter_field(field):
    print(field)
    if field is None:
        return "NULL"
    elif field == "0000-00-00":
        return "''"
    else:
        return "'{0}'".format(field)
