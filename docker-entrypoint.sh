#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -U ${DB_USER} > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting application..."
exec "$@"
