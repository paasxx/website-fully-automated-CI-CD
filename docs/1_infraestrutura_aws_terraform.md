# Documentação - Infra AWS com Terraform


### Estrutura de Pastas 

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

---

### Visão Geral

Este projeto implementa uma infraestrutura completa na AWS usando **Terraform**, com separação de ambientes (`dev`, `prod`), backend remoto versionado (S3 + DynamoDB), serviços em containers com **ECS Fargate**, e tráfego roteado por dois **Application Load Balancers (ALBs)** distintos para o frontend e backend.

Todos os recursos foram projetados para isolamento, escalabilidade, automação via pipelines e segurança em ambiente de nuvem.

### Componentes Provisionados

#### 1. Backend Remoto (bootstrap-backend)

- **S3 Bucket:** Armazena o estado Terraform (`terraform.tfstate`)
- **DynamoDB Table:** Controle de concorrência com locks

#### 2. Módulo de Infraestrutura (infrastructure)

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


#### 3. Hosted Zone & ACM (hosted\_zone\_acm)

- **Hosted Zone:** `candlefarm.com.br`
- **Certificados SSL:**
  - `www.candlefarm.com.br` (frontend)
  - `api.candlefarm.com.br` (backend API)
- **Registros DNS:**
  - `A` - `www.candlefarm.com.br` apontando para ALB do frontend
  - `A` - `api.candlefarm.com.br` apontando para ALB do backend


#### 4. Cuidados com Gerenciamento Manual

- Recursos gerenciados via Terraform **NÃO** devem ser removidos manualmente pela AWS Console
- O controle completo do ciclo de vida da infraestrutura é feito pelas pipelines


### Benefícios

- Infraestrutura como código (IaC)
- Modularidade e reutilização com Terraform modules
- Separacão de ambientes (`dev`, `prod`)
- Escalável, segura e auditável
- 100% automatizada via CI/CD

---

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

### 9. ECR repositório
Cria o local de armazenamento e build dos dockerfiles.

---

**Próximo:** `docs/2_ci_cd_pipelines.md` - Documentação das pipelines

