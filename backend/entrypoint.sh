#!/bin/sh

# Espera o banco de dados estar pronto
# /usr/local/bin/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "Database is up"


# Adiciona um atraso de 10 segundos
sleep 20


# Executa as migrações
python manage.py makemigrations
python manage.py migrate

# Inicia o servidor Django
exec python manage.py runserver 0.0.0.0:8000