## Con este comando generamos los archivos estaticos (comando obligatorio)
python manage.py collectstatic

## Con este comando creamos el super usuario inicial
python manage.py createsuperuser

## Ejecutar migraciones
python manage.py migrate

## Poner en marcha Redis (Windows)
redis-server

## Poner en marcha Celery worker
celery -A ibartionmap worker --loglevel=info

## Poner en marcha Celery beat
celery -A ibartionmap beat -l info

## Poner en marcha Celery worker/beat
celery -A ibartionmap worker --beat -l info -S django

## Eliminar tareas pendientes de celery redis
celery -A ibartionmap purge