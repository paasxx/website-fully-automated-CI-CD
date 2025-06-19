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

.
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
