#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h ${DB_HOST} -p ${DB_PORT:-5432} -U ${DB_USER} > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Warning: collectstatic failed, but continuing..."

echo "Starting application..."
exec "$@"
