#!/bin/sh

/usr/local/bin/wait-for-it.sh db-service.db.local:5432 --timeout=120 --strict -- echo "Database is up"

python /app/test_db_connection.py
if [ $? -ne 0 ]; then
  echo "Database connection test failed. Exiting..."
  exit 1
fi

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input

gunicorn fintrack.wsgi:application --bind unix:/tmp/gunicorn.sock --workers 3 --timeout 250 &

nginx -g "daemon off;"
