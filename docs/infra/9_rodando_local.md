# Rodando o Projeto Localmente com Docker Compose

Este guia mostra como subir, derrubar e interagir com os containers do projeto localmente usando Docker Compose, especificando o arquivo de configuração com a flag `-f`.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado

## Subindo o ambiente

1. **No diretório (/docker-compose), execute:**

   ```bash
   docker-compose -f docker-compose.dev.yml up -d --build
   ```

   - Substitua `docker-compose.dev.yml` pelo nome do arquivo que deseja usar.
   - O parâmetro `-d` executa em modo "detached" (em background).
   - O parâmetro `--build` força a reconstrução das imagens.

2. **Verifique se os containers estão rodando:**
   ```bash
   docker ps
   ```

## Containers disponíveis

- **fintrack-db**: Banco de dados Postgres
- **back**: Backend Python/Django
- **front**: Frontend React/Node

## Acessando os containers

Como os containers de backend e frontend sobem em modo "stand by", é necessário acessar cada um e iniciar manualmente o serviço.

### 1. Entrar no container do backend

```bash
docker exec -it back bash
```

- Para sair do container use o comando abaixo.

  ```bash
  exit
  ```

- Para rodar as migrações (se necessário):
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```
- Para iniciar o servidor Django:
  ```bash
  python manage.py runserver 0.0.0.0:8000
  ```

### 2. Entrar no container do frontend

```bash
docker exec -it front bash
```

- Para iniciar o servidor React:
  ```bash
  npm start
  ```

### 3. Entrar no container do banco de dados

```bash
docker exec -it fintrack-db bash
```

- Para acessar o psql:
  ```bash
  psql -U fintrack_user -d fintrack_db
  ```

## Parando e removendo os containers

Para derrubar todo o ambiente:

```bash
docker-compose -f docker-compose.dev.yml down
```

- Isso para e remove todos os containers, redes e volumes anônimos criados pelo `up`.

## Seed de dados / teste de escalabilidade

Para popular o banco com transações sintéticas (testar performance com muitos registros), use o comando `seed`. Ele gera transações direto no banco — **sem passar pelos parsers** — variando descrições (cobrindo todas as categorias do usuário), bancos, valores e datas ao longo de N anos.

**Pré-requisito:** o usuário-alvo já deve estar registrado pelo app (as categorias nascem no registro).

1. Crie seu config local a partir do template (o `seed_config.yml` é gitignorado):

   ```bash
   cp backend/fintrack/finances/seed_config.example.yml backend/fintrack/finances/seed_config.yml
   ```

2. Edite `backend/fintrack/finances/seed_config.yml`:

   ```yaml
   email: teste@gmail.com       # usuário registrado
   count: 1_000_000             # quantas transações gerar
   years: 3                     # espalha as datas nos últimos N anos
   banks: [nubank, inter, btg]  # bank sorteado por linha
   credit_ratio: 0.10           # % de créditos/pagamentos
   installment_ratio: 0.15      # % de parcelados (entre os não-crédito)
   unknown_ratio: 0.10          # % sem match -> cai em "Other"
   batch_size: 5000             # linhas por bulk_create
   seed: 42                     # fixa o RNG (remova para aleatório)
   ```

3. Rode:

   ```bash
   make seed
   ```

   > Para 1M linhas leva alguns minutos (o `categorize()` roda linha a linha). O progresso aparece como `5000/1000000` no terminal.

### Limpando os dados

```bash
# Apaga SÓ as transações de um usuário (rápido — DELETE via SQL)
make clear-transactions EMAIL=teste@gmail.com

# Zera o banco INTEIRO (containers + volume postgres_data) — apaga tudo, todos os usuários
make clean
```

> Para 1M+ linhas, use `make clear-transactions` (DELETE via SQL) em vez do `.delete()` do ORM Django, que é lento nesse volume (carrega PKs e processa cascade/signals um a um).

## Observações

- O volume `postgres_data` garante persistência dos dados do banco mesmo após remover os containers.
- O bind mount (`./backend/fintrack:/app` e `./frontend/front:/app`) permite que alterações no código local sejam refletidas imediatamente nos containers.

## Estrutura dos Dockerfiles

- **Backend**: `backend/Dockerfile.local`
- **Frontend**: `frontend/DockerFile.dev` _(Atenção ao nome, deve ser igual ao especificado no `docker-compose.yml`)_

---

> **TIP:** Sempre aguarde o banco de dados estar pronto antes de rodar comandos de migração ou iniciar o backend.

---

**Pronto! Agora você pode desenvolver e testar o projeto localmente usando Docker Compose.**

# Bind Mounts e `node_modules`

Durante o desenvolvimento local, este projeto utiliza **Docker Compose** com **bind mounts** para mapear o código-fonte local diretamente para os containers. Essa abordagem permite alta produtividade no desenvolvimento React + Django, com hot reload, sem rebuild da imagem a cada mudança. No entanto, é importante compreender os efeitos colaterais e como tratá-los corretamente.

---

## O que é um Bind Mount?

Um **bind mount** monta uma pasta do seu host (seu computador local) **dentro de um container**. Por exemplo:

```yaml
frontend:
  volumes:
    - ../frontend/front:/app # Monta o código local no container
```

Neste exemplo, tudo que estiver em `../frontend/front` será montado sobre `/app` dentro do container. Isso permite que:

- Arquivos editados localmente reflitam instantaneamente no container.
- O contrário também é verdadeiro, arquivos criados dentro do container, vão aparecer inesperadamente no seu diretório local. Como instalação do node modules, arquivos de migração de banco de dados no backend entre outros.

---

## Problema: `node_modules` desaparece

Quando você monta uma pasta como `/app`, **todo o conteúdo existente naquela pasta no container é sobrescrito pelo conteúdo local**. Ou seja:

- Se você instalou as dependências com `npm install` no Dockerfile...
- E **localmente não tem uma pasta `node_modules`**...
- A instalação desaparece dentro do container.

Isso gera erros como:

- `"Module not found"`
- `"Cannot find module 'react'"`
- React App não carrega

---

## Solução: Usar volume anônimo para `/app/node_modules`

A solução é adicionar um **volume anônimo** que preserve o conteúdo de `/app/node_modules` dentro do container, mesmo após o bind mount da pasta `/app`.

```yaml
frontend:
  volumes:
    - ../frontend/front:/app # Código-fonte local
    - /app/node_modules # Volume anônimo (preserva dependências)
```

Esse volume anônimo instrui o Docker a **manter um volume separado apenas para `node_modules`**, protegendo as dependências instaladas durante o build da imagem.

---

## Como funciona na prática?

1. Você faz o `docker build`, e o `Dockerfile.local` do React instala os pacotes (`npm install`).
2. Depois, o bind mount (`../frontend/front:/app`) monta a pasta do host no container, **sobrescrevendo tudo** — exceto o que está explicitamente isolado com volume.
3. O volume `/app/node_modules` continua existindo, **preservando as dependências**.
4. O container React roda normalmente, mesmo que você não tenha rodado `npm install` localmente.

---

## Exemplo real no projeto

```yaml
frontend:
  image: front
  container_name: front
  build:
    context: ../frontend
    dockerfile: Dockerfile.local
  volumes:
    - ../frontend/front:/app # Bind mount do código local
    - /app/node_modules # Protege dependências internas
  ports:
    - "3000:3000"
```

Esse padrão também pode ser usado em projetos Node.js, Next.js e qualquer outro que instale pacotes.
