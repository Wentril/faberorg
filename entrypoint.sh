#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST:-postgres} ${DATABASE_PORT:-5432}; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

#echo "Collecting static files..."
#python manage.py collectstatic --noinput --clear

echo "Loading initial data..."
python manage.py loaddata users projects working_groups topics user_memberships

exec "$@"
