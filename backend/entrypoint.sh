#!/bin/sh

# Espera o banco de dados estar pronto
/usr/local/bin/wait-for-it.sh db-service.db.local:5432 --timeout=60 --strict -- echo "Database is up"

# Executa o teste de conexão com o banco de dados
python /app/test_db_connection.py
if [ $? -ne 0 ]; then
  echo "Database connection test failed. Exiting..."
  exit 1
fi


# Executa as migrações
python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic --no-input

# Verifica se o superusuário já existe antes de criá-lo
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
" | python manage.py shell

# Insere registros no modelo Cobranca, se ainda não existirem
echo "
from cobrancas.models import Cobranca;
if not Cobranca.objects.filter(uuid='uuid-1').exists():
    Cobranca.objects.create(nome='Cliente 1', documento='12345678901', email='cliente1@example.com', valor='100.00', data_vencimento='2024-09-01', uuid='uuid-1');
if not Cobranca.objects.filter(uuid='uuid-2').exists():
    Cobranca.objects.create(nome='Cliente 2', documento='98765432109', email='cliente2@example.com', valor='200.00', data_vencimento='2024-09-15', uuid='uuid-2')
" | python manage.py shell

# Inicia o servidor Django com Gunicorn
gunicorn kanastra.wsgi:application --bind unix:/tmp/gunicorn.sock --workers 3 --timeout 250 &

# Inicia o servidor Nginx
nginx -g "daemon off;"