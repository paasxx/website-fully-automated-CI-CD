# Terraform AWS Infrastructure - README

Este projeto representa uma aplicação moderna e desacoplada com frontend em React e backend em Django, ambos dockerizados e orquestrados por ECS Fargate na AWS. Toda a infraestrutura é provisionada via **Terraform** com separação de ambientes (`dev`, `prod`) e backend remoto utilizando **S3 e DynamoDB** para controle de estado. O tráfego externo é roteado por **dois Application Load Balancers (ALBs)** independentes com **certificados HTTPS provisionados automaticamente via ACM**, e **DNS gerenciado pelo Route 53**. Todo o processo de deploy, provisionamento e destruição é **automatizado por pipelines GitHub Actions**, permitindo controle total da infraestrutura de qualquer lugar do mundo.

A estrutura foi desenhada com foco em escalabilidade, manutenibilidade e separação de responsabilidades entre infraestrutura, deploy de serviços e configuração de domínio e certificados.

> Observação: Tentativas de deploy duplicadas resultam em erro, pois o Terraform detecta recursos existentes e evita recriação, promovendo robustez e controle de custos. A pipeline de destruição remove absolutamente todos os recursos, incluindo o backend remoto em S3 e DynamoDB, garantindo que **nenhum recurso remanescente gere custo na AWS**. O projeto pode ser destruído completamente em menos de 5 minutos e reerguido em cerca de 15 minutos.

## Visão Geral da Arquitetura

- **Frontend:** React servido por Nginx atrás de um ALB
- **Backend:** Django com Gunicorn + Nginx, atrás de outro ALB
- **ALBs:** Dois Application Load Balancers independentes, com listeners HTTPS (porta 443)
- **DNS:** Gerenciado por Route 53 (`www` e `api`)
- **SSL:** Certificados provisionados via ACM e validados automaticamente por DNS
- **Terraform State:** Gerenciado remotamente com S3 e locks por DynamoDB

## Estrutura de Pastas

```
terraform/
├── bootstrap-backend/     # Criação do S3 + DynamoDB
├── dev/                   # Infraestrutura ambiente de desenvolvimento
├── prod/                  # Infraestrutura ambiente de produção
└── modules/               # Módulos reutilizáveis (infraestrutura, DNS, ACM, etc)
```

## Recursos Criados

### Backend Remoto (bootstrap-backend)

- **S3 Bucket:** Armazena o estado Terraform (`terraform.tfstate`)
- **DynamoDB Table:** Controle de concorrência com locks

### Hosted Zone & ACM (hosted\_zone\_acm)

- **Hosted Zone:** `candlefarm.com.br`
- **Certificados SSL:**
  - `www.candlefarm.com.br` (frontend)
  - `api.candlefarm.com.br` (backend)
- **Registros DNS:**
  - Tipo `A` apontando os subdomínios para os respectivos ALBs

### Módulo de Infraestrutura (infrastructure)

- **VPC:** Com subnets públicas (alta disponibilidade)
- **Security Groups:** Controlam o tráfego entre ALBs, ECS e RDS
- **ECS Clusters:** Frontend e backend isolados
- **Target Groups:** Associados aos ALBs (porta 80 frontend, 8000 backend)
- **RDS PostgreSQL:** Privado e acessível apenas pelo backend
- **IAM Roles:** Permissões finas para tasks e serviços

## Fluxo de Conexão

```
Usuário → ALB Frontend (443) → Nginx (porta 80)
       → proxy /api/ → ALB Backend (443) → Nginx (porta 8000) → Gunicorn (UNIX socket)
```

## Docker e Nginx (Frontend)

### nginx.conf.template

```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 150M;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass ${REACT_APP_BACKEND_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 250s;
        proxy_send_timeout 250s;
        proxy_read_timeout 250s;
    }
}
```

### Dockerfile (Frontend)

```Dockerfile
FROM node:16 as builder

WORKDIR /app
COPY front/ /app

RUN npm install --silent
RUN npm install axios --silent
RUN npm rebuild node-sass --silent
RUN npm run build

FROM nginx:latest

RUN apt-get update && apt-get install -y gettext-base

COPY nginx.conf /etc/nginx/templates/nginx.conf.template
COPY --from=builder /app/build /usr/share/nginx/html

CMD ["sh", "-c", "envsubst '${REACT_APP_BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
```

### axiosConfig.js

```js
const axiosInstance = axios.create({
    baseURL: '/api',
    timeout: 250000,
});
```

## CI/CD e Automação

O projeto é totalmente automatizado por **quatro pipelines desacopladas** via GitHub Actions:

### 1. Pipeline de Infraestrutura

- Provisiona a VPC, ECS, ALBs, RDS, Security Groups, roles
- Configura o backend remoto (S3 + DynamoDB)
- Estrutura base da aplicação

### 2. Pipeline de DNS (Hosted Zone)

- Cria a zona pública no Route 53
- Aponta os domínios `www` e `api` para os respectivos ALBs

### 3. Pipeline de Certificados ACM (HTTPS)

- Solicita e valida certificados com DNS automático
- Associa os certificados aos ALBs nos listeners HTTPS

### 4. Pipeline de Destruição Completa

- Remove recursos com segurança e ordem
- Mantém consistência com o estado remoto
- Remove inclusive o backend remoto (S3 + DynamoDB), eliminando **todos os recursos da AWS**

> A arquitetura é modular, versionada, replicável, escalável e segura. Pode ser executada remotamente via GitHub App, sem necessidade de CLI ou conexão local.

## Portas Utilizadas

- **443:** HTTPS externo via ALBs
- **80:** HTTP interno para containers ECS
- **8000:** Gunicorn (backend)
- **5432:** PostgreSQL (RDS)

## Considerações Técnicas

- A variável `REACT_APP_BACKEND_URL` é injetada **em tempo de execução** (runtime), e não em build time
- O template `nginx.conf` utiliza `envsubst` para adaptar dinamicamente o endereço do backend
- Essa abordagem evita rebuild de imagem e torna o container mais flexível

## Gerenciamento de Domínio (GoDaddy)

- Após provisionar a hosted zone, copie os Name Servers para o painel DNS do registrador (GoDaddy)
- A propagação pode levar até 48 horas, mas geralmente ocorre em poucas horas

## Cuidados com Gerenciamento Manual

- Recursos gerenciados via Terraform não devem ser removidos manualmente pela AWS Console
- Se for necessário, use `terraform state rm` para manter a integridade do estado
- O controle completo do ciclo de vida da infraestrutura é feito pelas pipelines

---

Autor: Pedro André\
Data: Junho 2025

















# Terraform AWS Infrastructure - README

Este documento descreve a infraestrutura automatizada criada com Terraform para provisionar uma aplicação com frontend e backend hospedados na AWS, com alta disponibilidade, escalabilidade, certificados SSL, e DNS configurado via Route 53. A estrutura de pastas está organizada de forma modular e por ambiente (dev e prod), com backend remoto em S3/DynamoDB para versionamento do estado.

## 🌐 Visão Geral da Arquitetura

* **Frontend**: Aplicação React servida atrás de um Load Balancer (HTTPS)
* **Backend**: API Django servida atrás de outro Load Balancer (HTTPS)
* **Load Balancer**: Dois ALBs distintos com listeners HTTPS (porta 443)
* **Route 53**: Gerenciamento de domínio e subdomínios (www e api)
* **ACM (AWS Certificate Manager)**: Certificados SSL emitidos e validados via DNS
* **Terraform Backend**: Armazenamento do estado remoto em S3 e controle de concorrência com DynamoDB

## 🗂️ Estrutura de Pastas

```bash
terraform/
├── main.tf                  # Provider principal
├── outputs.tf               # Outputs globais
├── variables.tf             # Variáveis globais
├── dev.tfvars               # Variáveis específicas do ambiente dev
├── bootstrap-backend/       # Setup do backend remoto
│   ├── bucket_s3.tf
│   ├── dynamodb.tf
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   └── dev.tfvars
├── dev/
│   ├── backend.tf           # Backend remoto
│   ├── dev.tfvars           # Variáveis dev
│   ├── main.tf              # Entrypoint do ambiente dev
│   ├── outputs.tf
│   ├── variables.tf
│   ├── versions.tf
│   └── modules/
│       ├── hosted_zone_acm/ # Certificados e DNS
│       │   ├── main.tf
│       │   ├── outputs.tf
│       │   └── variables.tf
│       └── infrastructure/  # Infra principal
│           ├── dev.tfvars
│           ├── main.tf
│           ├── outputs.tf
│           └── variables.tf
└── prod/                    # Ambiente prod (em construção)
    ├── main.tf
    ├── outputs.tf
    ├── prod.tfvars
    ├── variables.tf
    └── versions.tf
```

## 🔧 Recursos Criados

### 🪣 Backend Remoto (bootstrap-backend)

* **S3 Bucket**: `meu-bucket-terraform-pedro-silveira`

  * Armazena os estados (`terraform.tfstate`)
* **DynamoDB Table**: `terraform-locks`

  * Gerencia locks para evitar concorrência no deploy

### 🌍 Hosted Zone & ACM (hosted\_zone\_acm)

* **Route53 Hosted Zone**: `candlefarm.com.br`
* **Certificados SSL**:

  * `www.candlefarm.com.br`
  * `api.candlefarm.com.br`
* **Validações DNS**: Criadas automaticamente para os certificados via Route 53
* **Registros DNS**:

  * `A` - `www.candlefarm.com.br` apontando para ALB do frontend
  * `A` - `api.candlefarm.com.br` apontando para ALB do backend
* **Listeners HTTPS (443)** para ambos os ALBs com certificados ACM

### 🏗️ Módulo de Infraestrutura (infrastructure)

* **ECS Clusters** para frontend e backend
* **ALBs separados**:

  * Frontend: listener HTTPS 443 → target group na porta 80
  * Backend: listener HTTPS 443 → target group na porta 80
* **RDS PostgreSQL**:

  * Banco de dados privado acessível apenas pela VPC do backend
* **Security Groups**:

  * Controlam acesso entre ALB, ECS e RDS
* **VPC com subnets públicas e privadas**
* **IAM Roles** para ECS tasks e serviços

## 📎 Conexões e Dependências

```
[terraform init] -> S3 + DynamoDB (backend remoto)

main.tf (dev) usa:
  ├── module infrastructure
  │   ├── cria LB frontend/backend, ECS, SG, RDS
  └── module hosted_zone_acm
      ├── recebe infos do infra: lb_dns, lb_id, lb_arn, target_group_arn
      ├── cria certificados ACM e validações DNS
      ├── configura records na zone do Route53
```

## 🚪 Portas Utilizadas

* **443 (HTTPS)**: Load Balancers (externo)
* **80 (HTTP)**: Target Groups (interno ECS)
* **5432**: Acesso ao RDS (interno)

## 📄 Como Subir a Infraestrutura

```bash
# 1. Inicialize o backend remoto (1ª vez)
cd terraform/bootstrap-backend
terraform init
terraform apply -var-file=dev.tfvars

# 2. Suba a infraestrutura principal (dev)
cd ../dev
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

## 📤 Outputs Relevantes

* `frontend_cert_arn`
* `backend_cert_arn`
* `route53_ns_records`
* Load Balancer DNS + Zone IDs

## 🧠 Sugestões de Melhoria

* Separar estados por ambiente (`dev.tfstate`, `prod.tfstate`, etc)
* Adicionar monitoramento (CloudWatch logs, alarms)
* Inserir escalabilidade automática (Auto Scaling)
* Incluir CI/CD via GitHub Actions
* Modularizar ainda mais (RDS, ECS, VPC em módulos separados)

## 🖼️ Diagrama

O diagrama da arquitetura completa pode ser visualizado com base nas conexões descritas acima. Você pode utilizar o [draw.io](https://app.diagrams.net/) e seguir o seguinte guia:

* Comece com `S3` e `DynamoDB` no topo
* Conecte com `Terraform` simbolizando o backend remoto
* Crie dois caminhos para ALB do frontend e backend
* Conecte os ALBs com ECS Services
* Adicione `RDS` para o backend
* Coloque o `Route53` com apontamentos DNS e ACM

---

Essa documentação cobre todos os recursos, conexões e arquitetura da infraestrutura provisionada com Terraform na AWS. Ideal para consulta pessoal ou colaboração em equipe.


### Estrutura de pastas

```bash
├── README.md
├── docker-compose/
│   ├── docker-compose-tests.yml
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── run_tests.yml
│       ├── terraform_deploy_acm_https.yml
│       ├── terraform_deploy_antiga.yml
│       ├── terraform_deploy_hosted_zone.yml
│       ├── terraform_deploy_infra.yml
│       └── terraform_destroy.yml
├── frontend/
│   ├── Dockerfile
│   ├── DockerfileProd
│   ├── docker-compose-front.yml
│   ├── nginx.conf
│   └── front/
│       ├── README.md
│       ├── package.json
│       ├── package-lock.json
│       ├── public/
│       │   ├── favicon.ico
│       │   ├── index.html
│       │   ├── logo192.png
│       │   ├── logo512.png
│       │   ├── manifest.json
│       │   └── robots.txt
│       └── src/
│           ├── App.js
│           ├── App.test.js
│           ├── fonts.css
│           ├── index.js
│           ├── logo.svg
│           ├── reportWebVitals.js
│           ├── setupTests.js
│           ├── components/
│           │   ├── axiosConfig.js
│           │   ├── Navbar.js
│           │   ├── UploadCSV.js
│           │   ├── UploadedFilesContext.js
│           │   └── UploadedFilesList.js
│           ├── styles/
│           │   ├── main.scss
│           │   ├── components/
│           │   │   ├── Button.scss
│           │   │   ├── Cards.scss
│           │   │   ├── Files.scss
│           │   │   ├── Navbar.scss
│           │   │   ├── Spinner.scss
│           │   │   └── UploadForm.scss
│           │   ├── layouts/
│           │   │   ├── Background.scss
│           │   │   ├── Footer.scss
│           │   │   └── Header.scss
│           │   └── global/
│           │       ├── Mixins.scss
│           │       ├── Reset.scss
│           │       └── Variables.scss
├── backend/
│   ├── Dockerfile
│   ├── DockerfileProd
│   ├── docker-compose-back.yml
│   ├── nginx.conf
│   ├── requirements.txt
│   ├── test_db_connection.py
│   ├── wait-for-it.sh
│   ├── entrypoint.sh
│   └── kanastra/
│       ├── manage.py
│       ├── run.sh
│       ├── tests.sh
│       ├── cobrancas/
│       │   ├── __init__.py
│       │   ├── admin.py
│       │   ├── apps.py
│       │   ├── email_engine.py
│       │   ├── models.py
│       │   ├── urls.py
│       │   ├── views.py
│       │   ├── migrations/
│       │   │   └── __init__.py
│       │   └── tests/
│       │       ├── __init__.py
│       │       ├── input.csv
│       │       └── test_views.py
│       └── kanastra/
│           ├── __init__.py
│           ├── asgi.py
│           ├── settings.py
│           ├── urls.py
│           └── wsgi.py
├── terraform/
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   ├── dev.tfvars
│   ├── bootstrap-backend/
│   │   ├── bucket_s3.tf
│   │   ├── dynamodb.tf
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── variables.tf
│   │   └── dev.tfvars
│   ├── dev/
│   │   ├── backend.tf
│   │   ├── dev.tfvars
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── variables.tf
│   │   ├── versions.tf
│   │   └── modules/
│   │       ├── hosted_zone_acm/
│   │       │   ├── main.tf
│   │       │   ├── outputs.tf
│   │       │   └── variables.tf
│   │       └── infrastructure/
│   │           ├── dev.tfvars
│   │           ├── main.tf
│   │           ├── outputs.tf
│   │           └── variables.tf
│   └── prod/
│       ├── main.tf
│       ├── outputs.tf
│       ├── prod.tfvars
│       ├── variables.tf
│       └── versions.tf
```


# Documentação de Integração Frontend ↔ Backend com Load Balancers (AWS ECS + Nginx)

## 🌐 Visão Geral

Este projeto consiste em um frontend React e um backend Django, ambos hospedados em contêineres ECS (Fargate), cada um com seu próprio Load Balancer (ALB). A comunicação entre o frontend e o backend é feita via **Nginx**, utilizando o path `/api/` como proxy.

## 📦 Estrutura e Comunicação

```
[ Usuário ]
    ↓
[ Load Balancer do Frontend ]
    ↓ (Nginx: /api/*)
[ Frontend Container Nginx ]
    ↓ (proxy_pass http://LB_backend/api/)
[ Load Balancer do Backend ]
    ↓
[ Backend Django + Gunicorn + Nginx ]
```

- O React faz chamadas `axios.post('/api/upload-csv')`
- O Nginx do frontend intercepta `/api/` e **roteia para o Load Balancer do backend**
- O backend responde e o frontend mostra o resultado

## ⚙️ Backend URL

O backend é configurado dinamicamente com:

```hcl
# Terraform (frontend ECS Task)
environment = [
  {
    name  = "REACT_APP_BACKEND_URL"
    value = "http://${aws_lb.backend_lb.dns_name}/api"
  }
]
```

Essa variável é usada no build do React e também no template `nginx.conf.template`.

---

## 📁 nginx.conf do Frontend

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 150M;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass ${REACT_APP_BACKEND_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 250s;
        proxy_send_timeout 250s;
        proxy_read_timeout 250s;

        client_max_body_size 150M;
    }
}
```

> Usamos `envsubst` para substituir `${REACT_APP_BACKEND_URL}` em tempo de build.

---

## 🐳 Dockerfile do Frontend (Final)

```Dockerfile
FROM node:16 as builder

WORKDIR /app
COPY front/ /app

RUN npm install --silent
RUN npm install axios --silent
RUN npm rebuild node-sass --silent

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

FROM nginx:latest

RUN apt-get update && apt-get install -y gettext-base

COPY nginx.conf /etc/nginx/templates/nginx.conf.template

ENV REACT_APP_BACKEND_URL=http://localhost/api

RUN envsubst '${REACT_APP_BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/build /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]
```

---

## 📦 React - Ajustes Necessários

### 1. **Todos os endpoints devem começar com `/api/`**:

```javascript
// axiosConfig.js
const axiosInstance = axios.create({
    baseURL: '/api',
    timeout: 250000,
});
```

### 2. No código (exemplo):

```javascript
await axiosInstance.post('/upload-csv/', formData);
// Torna-se:
await axiosInstance.post('/api/upload-csv/', formData);
```

### 3. Não use `REACT_APP_BACKEND_URL` no axios diretamente. As chamadas devem ser relativas (`/api/...`), pois o Nginx faz o roteamento.

---

## ✅ Conclusão

- Toda requisição do React passa pelo Load Balancer do frontend.
- O Nginx do frontend roteia para o backend, usando `/api/` como prefixo.
- O Terraform injeta dinamicamente o endereço correto do Load Balancer do backend.
- O Dockerfile e o Nginx são configurados para aceitar uploads grandes e realizar substituições com `envsubst`.

---

**Autor**: Pedro André  
**Data**: Junho 2025  


# Documentação Técnica: Arquitetura Nginx, React, AWS ECS com Load Balancers

## Visão Geral da Arquitetura
Este projeto utiliza um frontend React e um backend Django (via Gunicorn), ambos servidos em containers Docker na AWS Fargate. A comunicação entre os serviços é feita através de Load Balancers (ALBs) e o tráfego é roteado com Nginx.

Abaixo está o fluxo geral:

```
Usuário (Navegador)
   |
   v
Load Balancer do Frontend (porta 80 e 443)
   |
   v
Container do Frontend (porta 80 com Nginx)
   | (via proxy_pass no Nginx frontend para /api)
   v
Load Balancer do Backend (porta 80 e 443)
   |
   v
Container do Backend (porta 8000 com Gunicorn e Nginx)
```

---

## Camadas, Conexões e AWS Detalhada (VPC, SGs, Target Groups)

### Passo a Passo Completo do Fluxo:

1. **Usuário (Navegador)** acessa o site via `http://frontend-alb`
2. A requisição entra no **Load Balancer do Frontend**, que:
   - Escuta nas portas **80 e 443** (HTTP e HTTPS preparado)
   - Está ligado a um **Security Group (frontend_lb_sg)** que:
     - Permite `Ingress` nas portas 80/443 de qualquer IP (0.0.0.0/0)
     - Permite `Egress` irrestrito (0.0.0.0/0)
3. O ALB roteia a requisição para o **Target Group do Frontend**, que:
   - Está configurado para direcionar para porta **80** dos containers
   - Está associado ao **ECS Fargate do Frontend**
4. O container do frontend:
   - Escuta na porta **80** via Nginx
   - Serve arquivos estáticos e intercepta `/api/*` com proxy_pass
   - Usa seu próprio **Security Group (frontend_sg)** que:
     - Permite `Ingress` na porta 80 vindo **somente** do `frontend_lb_sg`
     - Permite `Egress` irrestrito

5. Quando o React (com `axios`) chama uma rota `/api/...`, o Nginx faz:
   - `proxy_pass` para o **Load Balancer do Backend** (backend-alb)
6. O **Load Balancer do Backend**:
   - Escuta nas portas **80 e 443** (HTTP e HTTPS preparado)
   - Usa o **SG backend_lb_sg**, que:
     - Permite `Ingress` na 80/443 vindo **do frontend_sg** e também público (para testes)
     - `Egress` irrestrito
7. O backend-alb envia ao seu **Target Group**, que:
   - Está configurado para porta **8000** dos containers do backend
   - Aponta para containers no **ECS Fargate do Backend**
8. O container backend:
   - Escuta na porta **8000**, onde o Nginx faz proxy para o Gunicorn
   - Usa o **SG backend_sg**, que:
     - Permite `Ingress` na 8000 vindo **apenas do backend_lb_sg**
     - `Egress` irrestrito

9. Gunicorn (escutando via UNIX socket `/tmp/gunicorn.sock`) recebe a requisição final e responde.

10. A resposta faz o caminho inverso até o navegador do usuário.

---

## VPC e Subnets

Todos os componentes descritos acima estão dentro da mesma **VPC (dev_vpc)**, que:
- Tem DNS habilitado
- Possui **duas subnets públicas**, cada uma em uma zona de disponibilidade
- Os ALBs e containers ECS estão distribuídos nessas subnets para alta disponibilidade

---

## Funcionamento do Nginx (Frontend)

- `location /` → serve o React build (index.html e estáticos)
- `location /api/` → faz proxy_pass para o backend-alb (respeitando `/api` no caminho)
- `client_max_body_size` ajustado para permitir uploads grandes
- Barra no `proxy_pass` deve ser evitada para manter `/api/...` corretamente

---

## Funcionamento do Nginx (Backend)

- Escuta na porta 8000
- `location /api/` → proxy para Gunicorn (via socket)
- `location /static/` e `/media/` → servem arquivos diretamente
- Também ajustado com `client_max_body_size`

---

## axiosConfig.js no React

- Usa `baseURL: '/api'` para todas as chamadas
- O Nginx do frontend encaminha corretamente com `proxy_pass http://backend-alb/api` (sem barra final!)

```js
const axiosInstance = axios.create({
    baseURL: '/api',
    timeout: 250000,
});
```

---

## Considerações Finais

- Todas as permissões entre ALBs, containers e banco são controladas por **Security Groups** de forma clara e segura.
- O uso correto das portas (80/443, 8000) e `proxy_pass` com/sem barra é fundamental para o roteamento funcionar.
- A separação por ALB para cada serviço e os respectivos Target Groups garante isolamento e facilita futura escalabilidade.
- A VPC organiza todos os recursos em uma infraestrutura segura e controlada.


## Componentes AWS utilizados e suas funções

### 1. VPC (Virtual Private Cloud)
Rede privada onde todos os recursos AWS (ECS, ALB, etc.) estão isolados. Define o espaço de IPs (CIDR) e subnets públicas.

### 2. Subnets
Subdivisões da VPC, associadas a zonas de disponibilidade. Os containers ECS e os ALBs são distribuídos entre elas.

### 3. Security Groups (SG)
Firewalls virtuais que controlam tráfego de entrada (ingress) e saída (egress) por portas, protocolos e IPs.

### 4. Load Balancer (ALB)
Distribui o tráfego entre containers ECS:
- Frontend ALB escuta portas 80 e 443
- Backend ALB escuta portas 80 e 443

### 5. Listeners
Componente do ALB que define qual porta ouvir (80, 443) e qual ação tomar (ex: enviar tráfego a um Target Group).

### 6. Target Group
Define portas de destino (80 no frontend, 8000 no backend) e envia tráfego para os IPs dos containers ECS.

### 7. ECS Cluster
Agrupamento de serviços ECS Fargate (frontend e backend). Cada serviço gerencia seus containers e escalabilidade.

### 8. ECS Service
Mantém as tarefas (containers) rodando, associadas ao target group e load balancer.

---

## Diagrama do fluxo completo (resumido com setas)

```
Usuário (navegador)
  ↓
Frontend Load Balancer (portas 80 e 443)
  ↓ (via Target Group porta 80)
ECS Frontend (porta 80 com Nginx)
  ↓ (proxy_pass para backend)
Backend Load Balancer (portas 80 e 443)
  ↓ (via Target Group porta 8000)
ECS Backend (porta 8000 com Nginx)
  ↓ (proxy_pass para Gunicorn via UNIX socket)
Gunicorn (executando Django app)
```

Todos os elementos estão dentro da VPC com regras de segurança definidas por Security Groups.

# Deploy e CI/CD - Infraestrutura AWS com Terraform e Docker

Este projeto possui uma pipeline CI/CD organizada, segura e modular para provisionar infraestrutura na AWS, construir e publicar imagens Docker, configurar DNS e certificados HTTPS, e ainda destruir tudo quando necessário para evitar custos.

---

## Visão Geral daa Pipelines

### 1. Deploy da Infraestrutura

- Executado via GitHub Actions, workflow manual (`workflow_dispatch`) com senha para segurança.
- Utiliza **Terraform** para provisionar:
  - Bucket S3 (armazenamento remoto do estado Terraform)
  - Tabela DynamoDB (lock para evitar concorrência no estado Terraform)
  - Rede (VPC, subnets, security groups)
  - Load Balancers, Target Groups
  - Clusters ECS e serviços
  - Repositórios ECR para Docker images

### 2. Deploy da Hosted Zone (DNS)

- Executado após a infraestrutura principal.
- Configura zona DNS pública no **Route53**.
- Cria registros DNS para frontend (`www`) e backend (`api`).
- Essencial para apontar domínios para os Load Balancers.

### 3. Deploy do ACM (Certificado HTTPS)

- Executado após a Hosted Zone.
- Provisiona certificado SSL/TLS com **AWS Certificate Manager (ACM)**.
- Garante HTTPS válido para frontend e backend.
- Pipeline espera a propagação da zona DNS antes de aplicar o ACM.

### 4. Build e Push das Imagens Docker

- Executado após a infraestrutura estar provisionada.
- Utiliza Docker Buildx para build multiplataforma (linux/amd64).
- Faz login no Amazon ECR.
- Builda e envia as imagens Docker do backend e frontend para os repositórios ECR.

---

## Organização e Segurança

- As pipelines usam variáveis de ambiente com segredos do GitHub (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc).
- A execução manual exige senha para evitar execuções acidentais ou não autorizadas.
- O estado do Terraform é armazenado remotamente no S3 e DynamoDB, garantindo:
  - Controle de concorrência e bloqueios
  - Histórico e rastreabilidade de mudanças
- Os recursos são separados por módulos e ambientes (`dev`, `staging`, `prod`) usando arquivos `.tfvars`.

---

## Fluxo resumido

1. Usuário dispara o workflow manual no GitHub.
2. Terraform provisiona a infraestrutura base (VPC, ALBs, ECS, SGs).
3. Terraform provisiona a zona DNS no Route53 e cria os registros necessários.
4. Terraform provisiona o ACM para habilitar HTTPS.
5. Docker images são buildadas e enviadas para ECR.
6. Serviços ECS são atualizados com as novas imagens.
7. Tudo está pronto para rodar com HTTPS (após propagação DNS).

---

## Pipeline de Destruição (Destroy)

- Também executado manualmente com senha.
- Remove recursos AWS em ordem:
  - Remove repositórios ECR manualmente para evitar conflitos de estado.
  - Executa `terraform destroy` para infraestrutura principal.
  - Executa `terraform destroy` para hosted zone e ACM.
  - Limpa DynamoDB e S3 usados pelo backend remoto do Terraform.
- Garante que você possa eliminar tudo de forma rápida e segura, sem custos remanescentes.

---

## Benefícios desta abordagem

- **Automação total:** De infra a deploy, tudo via pipeline CI/CD.
- **Segurança:** Segredos gerenciados e execuções controladas.
- **Escalabilidade:** Infra modular e pronta para múltiplos ambientes.
- **Manutenção:** Estado remoto e controle de concorrência facilitam colaboração e histórico.
- **Flexibilidade:** Pode destruir tudo a qualquer momento com segurança.

---

Se precisar, posso gerar também um diagrama visual do fluxo do deploy para complementar a documentação!


# Configuração do Domínio e Considerações sobre Deleções Manuais

## Passo: Configurar os Name Servers no GoDaddy

Após a criação da **Hosted Zone** na AWS Route53 (via Terraform na pipeline), a AWS gera um conjunto de **Name Servers (NS)** exclusivos para sua zona DNS. 

### O que fazer:

1. **Acesse o painel do seu registrador de domínio** (exemplo: GoDaddy).
2. Localize a configuração de DNS para o domínio em questão.
3. Substitua os servidores DNS atuais pelos **Name Servers gerados na Hosted Zone da AWS**.
   - Essa informação é obtida via saída do Terraform (`terraform output`) ou diretamente no console AWS Route53.
4. Salve as alterações.

### Importante:

- A propagação dessas mudanças pode levar até 48 horas, mas normalmente é bem mais rápida (algumas horas).
- Durante esse período, o domínio começará a apontar para os Load Balancers provisionados na AWS, e o acesso ao site ficará disponível conforme a infraestrutura criada.

---

## Impacto de Deletar Recursos Manualmente na AWS

### O que acontece se um recurso for removido manualmente (fora do Terraform)?

- **Estado do Terraform fica inconsistente:** o Terraform mantém um arquivo de estado (`terraform.tfstate`) que "conhece" os recursos provisionados.
- Se você apagar um recurso manualmente, o Terraform ainda "acha" que ele existe no estado.
- Ao rodar um novo `terraform apply` ou `terraform plan`, podem ocorrer erros porque o recurso esperado não existe mais.
- Dependendo do recurso e dependências, isso pode causar:
  - **Falhas na pipeline** porque o Terraform tenta gerenciar algo inexistente.
  - **Recursos órfãos**, que ficam na AWS sem controle pelo Terraform.
  - Problemas de segurança, custo e manutenção.

### O Terraform é inteligente?

- O Terraform tem comandos para tentar "recuperar" do estado, como `terraform refresh` para sincronizar estado com a infraestrutura atual.
- Você pode remover um recurso do estado com `terraform state rm` para que o Terraform pare de gerenciá-lo.
- Porém, não é recomendado deletar recursos manualmente sem atualizar o estado Terraform, pois isso quebra a **sincronia e previsibilidade** da infraestrutura como código.

### Boas práticas para deletar recursos:

- Sempre tente deletar recursos via **Terraform** (executando `terraform destroy` ou removendo o recurso da configuração e rodando `terraform apply`).
- Se for necessário deletar manualmente, atualize o estado com `terraform state rm` para evitar inconsistências.
- Use a pipeline de **destroy** que já está configurada para limpar tudo com segurança e controle.

---

## Resumo

- Configurar os Name Servers no GoDaddy é fundamental para que o domínio funcione apontando para a AWS.
- Deletar recursos manualmente na AWS pode quebrar seu controle de infraestrutura e causar falhas na pipeline.
- Use sempre o Terraform para alterações e destruição para manter o ambiente consistente, seguro e fácil de manter.


### Estrutura revisada com a descoberta do erro da variavel REACT_APP_BACKEND_URL sendo atribuida durante o build, e que deveria ser atribuida so no runtime, pq o build eh feito no ECR e nao tem acesso ao ECS onde a variavel de mabiente esta, entao o CMD que rida no runtime que deve carregar a variavel.