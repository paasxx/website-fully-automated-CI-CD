#!/bin/sh

# # Espera o banco de dados estar pronto
# /usr/local/bin/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "Database is up"

# Adiciona um atraso de 10 segundos
sleep 20

# Executa as migrações
python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic

# Inicia o servidor Django com Gunicorn
gunicorn kanastra.wsgi:application --bind unix:/tmp/gunicorn.sock --workers 3 &

# Inicia o servidor Nginx
nginx -g "daemon off;"