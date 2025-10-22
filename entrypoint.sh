#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST:-postgres} ${DATABASE_PORT:-5432}; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

exec "$@"
