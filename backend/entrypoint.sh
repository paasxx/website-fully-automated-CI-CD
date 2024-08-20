#!/bin/sh

# # Espera o banco de dados estar pronto
# /usr/local/bin/wait-for-it.sh 127.0.0.1:5432 --timeout=60 --strict -- echo "Database is up"

# Espera até que o banco de dados esteja acessível
until pg_isready -h db -p 5432; do
  echo "Aguardando o banco de dados..."
  sleep 2
done


# Adiciona um atraso de 10 segundos
sleep 10

# Executa as migrações
python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic --no-input

# Cria um superusuário não interativo
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')" | python manage.py shell

# Inicia o servidor Django com Gunicorn
gunicorn kanastra.wsgi:application --bind unix:/tmp/gunicorn.sock --workers 3 --timeout 120 &

# Inicia o servidor Nginx
nginx -g "daemon off;"