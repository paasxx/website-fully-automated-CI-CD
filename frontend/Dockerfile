# Use a imagem oficial do Node como base
FROM node:latest

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos do projeto para o contêiner
COPY front/ /app

# Instala as dependências do projeto
RUN npm install && npm install axios && npm rebuild node-sass


# Abre a porta 3000 para acessar o servidor de desenvolvimento do React
EXPOSE 3000

# Comando para iniciar o servidor de desenvolvimento do React quando o contêiner for executado
# CMD ["npm", "start"]

#Comando para rodar o container porém sem iniciar npm start, que deve ser feito manualmente entrando no container.
CMD ["sleep", "infinity"]