# Use a imagem oficial do Python como base
FROM python:3.9


# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos do projeto para o contêiner
COPY kanastra/ /app

# Abre a porta 8000 para acessar o servidor Django
EXPOSE 8000

# Comando para iniciar o servidor Django quando o contêiner for executado
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
