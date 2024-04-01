# Kanastra Challenge

Este é o repositório do Desafio Kanastra. Nele, você encontrará informações sobre como instalar, executar e contribuir para o projeto.


## Como Começar

Siga os passos abaixo para executar o projeto.

### Pré-requisitos

1. Node.js para o frontend React

### Instalação


1. Clone este repositório em sua máquina local:

```bash
git clone https://github.com/paasxx/kanastra.git
```

2. Navegue até o diretório do frontend:

```bash
cd kanastra/frontend/front
```
E rode o comando para instalar os node_modules.
```bash
npm install
```

2.1 Certifique-se de ter o Docker e o Docker Compose instalados em sua máquina, volte na raiz do projeto kanastra/ onde o docker compose está e rode:

```bash
docker-compose up --build -d
```
2.2 Acesse o container do backend

```bash
docker exec -it back bash
```

2.3 Para executar as migrations no backend e os testes, você pode usar o script bash fornecido:

```bash
chmod +x run.sh
```

```bash
./run.sh
```

3. A página roda no link: `http://localhost:3000/`:
