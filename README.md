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

2. Navegue até o diretório do projeto:

```bash
cd projeto-kanastra
```

2.1 Certifique-se de ter o Docker e o Docker Compose instalados em sua máquina.

```bash
docker-compose up --build
```
2.2 Acesse o container do backend

```bash
docker exec -it back bash
```

2.3 Para executar as migrations no backend e o teste End to End, você pode usar o script bash fornecido:

```bash
chmod +x run.sh
```

```bash
./run.sh
```

4. O site deve carregar automaticamente no chrome senão no prompt é fornecido o link: `http://localhost:3000/`:


```

A API estará acessível em `http://127.0.0.1:5000/`.

### Endpoints da API

| Método   | Endpoint                    | Descrição                                      |
|----------|-----------------------------|------------------------------------------------|
| GET      | /                           | Hello World                                    |
| GET      | /listusers                  | Lista de Todos os usuários                     |
| DELETE   | /userdelete/<id>            | Deleta o usuário                               |
| GET      | /userdetails/<id>           | Recupera informações detalhadas de um usuário  |
| PUT      | /userupdate/<id>            | Atualiza os dados do usuário                   |
| POST     | /useradd                    | Adiciona um novo usuário ao banco de dados     |


### Parâmetros de entrada para Endpoints da API

Exemplo de parâmetro de entrada para os métodos PUT e POST no formato .json

```json
{
    "name": "Pedro André Aguiar da Silveira",
    "rg": "14496948",
    "cpf": "01587181608",
    "data_nascimento": "1992-01-31",
    "data_admissao": "2019-04-08"
}
```
