#!/bin/sh
# entrypoint.sh - waits for the database, applies migrations, then starts Gunicorn

set -e

echo "==> Waiting for PostgreSQL..."
until python -c "
import os, psycopg
try:
    psycopg.connect(
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
    )
    print('PostgreSQL is ready.')
except Exception as e:
    print(f'Not ready: {e}')
    exit(1)
"; do
  echo "PostgreSQL is unavailable - sleeping 2s"
  sleep 2
done

echo "==> Applying migrations..."
python manage.py migrate --settings=config.settings.dev

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings.dev

echo "==> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --worker-class gthread \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
