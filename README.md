# Descrição geral

Este projeto representa uma aplicação moderna e desacoplada com frontend em **React** e backend em **Django/Python**, ambos dockerizados e orquestrados por pipelines  de deploy/destroy no **GitHub Actions**, permitindo controle total da infraestrutura de qualquer lugar do mundo em poucos minutos. 

Toda a infraestrutura é provisionada via  **AWS** e **Terraform** com separação de ambientes (`dev`, `prod`) e backend remoto utilizando **S3 e DynamoDB** para controle de estado. 


A estrutura foi desenhada com foco em escalabilidade, manutenabilidade e separação de responsabilidades entre infraestrutura, deploy de serviços e configuração de domínio e certificados.

> Obs: Tentativas de deploy duplicadas são barradas, graças ao backend remoto **(S3 e DynamoDB)** que detecta recursos existentes e evita recriação, promovendo robustez. Com relação à pipeline de destruição, ela remove absolutamente todos os recursos, incluindo o backend remoto, garantindo que **nenhum recurso remanescente gere custo na AWS**. O projeto completo pode ser erguido em 10 minutos aproximadamente e destruído completamente em menos de 5 minutos.

## Visão Geral da Arquitetura

- **Frontend:** React servido por Nginx atrás de um ALB
- **Backend:** Django com Gunicorn + Nginx, atrás de outro ALB
- **ALBs:** Dois Application Load Balancers independentes, com listeners HTTP e HTTPS!
- **DNS:** Gerenciado por Route 53 (`www` e `api`)
- **SSL:** Certificados provisionados via ACM e validados automaticamente por DNS
- **Terraform State:** Gerenciado remotamente com S3 e locks por DynamoDB

## Funcionamento do Nginx (Frontend)

- Escuta na porta **80**
- `location /` → serve o React build (index.html e estáticos)
- `location /api/` → faz proxy_pass para o backend-alb (respeitando `/api` no caminho)
- `client_max_body_size` ajustado para permitir uploads grandes
- Barra no `proxy_pass` deve ser evitada para manter `/api/...` corretamente

---

## Funcionamento do Nginx (Backend)

- Escuta na porta **8000**
- `location /api/` → proxy para Gunicorn (via socket)
- `location /static/` e `/media/` → servem arquivos diretamente
- Também ajustado com `client_max_body_size`

---


## Recursos Criados

### Estrutura de Pastas do Terraform

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


### 1. Backend Remoto (bootstrap-backend)

- **S3 Bucket:** Armazena o estado Terraform (`terraform.tfstate`)
- **DynamoDB Table:** Controle de concorrência com locks

### 2. Módulo de Infraestrutura (infrastructure)

- **VPC:** Com subnets públicas (alta disponibilidade)
- **Security Groups:** Controlam o tráfego entre ALBs, ECS e RDS
- **ECS Clusters:** 
  - `frontend_service`: React + Nginx
  - `backend_service`: Django + Gunicorn + Nginx
- **Load Balancers:** 
  - Frontend: porta 443 (HTTPS) > porta 80 (ECS)
  - Backend: porta 443 (HTTPS) > porta 8000 (ECS)
- **Target Groups:** Associados aos ALBs (porta 80 frontend, 8000 backend) e porta 443 para HTTPS para cada ALB.
- **RDS PostgreSQL:** Privado e acessível apenas pelo backend
- **IAM Roles:** Permissões finas para tasks e serviços


### 3. Hosted Zone & ACM (hosted\_zone\_acm)

- **Hosted Zone:** `candlefarm.com.br`
- **Certificados SSL:**
  - `www.candlefarm.com.br` (frontend)
  - `api.candlefarm.com.br` (backend API)
- **Registros DNS:**
  - `A` - `www.candlefarm.com.br` apontando para ALB do frontend
  - `A` - `api.candlefarm.com.br` apontando para ALB do backend


### 4. Cuidados com Gerenciamento Manual

- Recursos gerenciados via Terraform **NÃO** devem ser removidos manualmente pela AWS Console
- O controle completo do ciclo de vida da infraestrutura é feito pelas pipelines


## CI/CD e Automação

O projeto é totalmente automatizado por **quatro pipelines** via **GitHub Actions**:

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



## Portas Utilizadas

- **443:** HTTPS externo via ALBs
- **80:** HTTP interno (frontend)
- **8000:** Gunicorn (backend)
- **5432:** PostgreSQL (RDS)



### Estrutura completa do projeto

```bash
├── README.md
├── docs/
│   ├── doc_1.md
│   └── doc_2.md
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
#### Obs: para mais detalhes consultar a documentação completa do projeto no diretório /docs.