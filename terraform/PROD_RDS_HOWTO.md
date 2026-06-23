# Como migrar para produção: Docker DB → RDS PostgreSQL

Guia completo, arquivo por arquivo, para transformar o ambiente `prod/` (hoje incompleto)
em uma stack de produção real com banco gerenciado.

---

## Diagnóstico: o que existe hoje vs o que é necessário

### Dev (funcionando)
```
ECS Cluster
  ├── frontend-service  → ECS Fargate (container Nginx+React)
  ├── backend-service   → ECS Fargate (container Django)
  └── db-service        → ECS Fargate (container Postgres)  ← efêmero, dados somem
       └── service discovery: db-service.db.local
```

### Prod (objetivo)
```
ECS Cluster
  ├── frontend-service  → ECS Fargate (container Nginx+React)
  └── backend-service   → ECS Fargate (container Django)

RDS PostgreSQL 16         ← banco gerenciado, persistente, backups automáticos
  └── endpoint: fintrack-prod.xxxxxxx.us-east-1.rds.amazonaws.com
```

### O que muda na prática
| Dev | Prod |
|-----|------|
| DB como container ECS | DB como RDS `aws_db_instance` |
| `db-service.db.local` (service discovery) | endpoint RDS (ex: `fintrack-prod.xxx.rds.amazonaws.com`) |
| Subnets públicas para tudo | Subnets públicas para ECS + privadas para RDS |
| Sem service discovery necessário | Sem service discovery |
| `DEBUG = True` | `DEBUG = False` |
| `SECRET_KEY` hardcoded | `SECRET_KEY` via variável de ambiente |
| `CORS_ALLOW_ALL_ORIGINS = True` | CORS restrito ao domínio |
| `terraform/prod/main.tf` incompleto | `terraform/prod/` com infra completa |

---

## Pré-requisitos

### GitHub Secrets necessários (adicionar antes de rodar a pipeline)

Acesse: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Valor | Já existe? |
|--------|-------|------------|
| `AWS_ACCESS_KEY_ID` | chave AWS | ✅ |
| `AWS_SECRET_ACCESS_KEY` | secret AWS | ✅ |
| `AWS_REGION` | `us-east-1` | ✅ |
| `AWS_ACCOUNT_ID` | ID da sua conta AWS | ✅ |
| `WORKFLOW_PASSWORD` | senha manual das pipelines | ✅ |
| `DB_PASSWORD` | senha do banco | ✅ |
| `DJANGO_SECRET_KEY` | chave secreta do Django | ⚠️ provavelmente não existe |

Para gerar um `DJANGO_SECRET_KEY` seguro:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### tfvars para prod

A pipeline lê `-var-file=prod.tfvars`. Você precisa criar esse arquivo.

**`terraform/prod/prod.tfvars`** (não commitar — adicionar ao `.gitignore`):
```hcl
aws_account_id   = "123456789012"
db_password      = "sua-senha-aqui"
django_secret_key = "sua-secret-key-aqui"
```

> Os valores sensíveis ficam no GitHub Secrets e são injetados pela pipeline.
> O arquivo local é só para rodar terraform manualmente se precisar.

---

## Arquitetura de rede para prod

O RDS **não deve ficar em subnet pública**. O padrão correto:

```
VPC 10.0.0.0/16
  ├── Subnet pública us-east-1a  (10.0.1.0/24) → ECS Frontend, ECS Backend, ALBs
  ├── Subnet pública us-east-1b  (10.0.2.0/24) → ECS Frontend, ECS Backend, ALBs
  ├── Subnet privada us-east-1a  (10.0.11.0/24) → RDS
  └── Subnet privada us-east-1b  (10.0.12.0/24) → RDS (subnet group precisa de 2 AZs)
```

O backend ECS fica na subnet pública mas o SG do RDS aceita conexão apenas do `backend_sg`.
Isso significa que o RDS não é acessível da internet, só do backend.

---

## Arquivo por arquivo — o que criar/modificar

### Estrutura final esperada em `terraform/prod/`

```
terraform/prod/
  ├── main.tf          ← REESCREVER completamente
  ├── variables.tf     ← ATUALIZAR (adicionar novas vars)
  ├── outputs.tf       ← ATUALIZAR
  ├── backend.tf       ← CRIAR (remote state S3 + DynamoDB)
  ├── versions.tf      ← já existe, ok
  └── prod.tfvars      ← CRIAR (não commitar)
```

---

### 1. `terraform/prod/backend.tf` — CRIAR

Remote state separado do dev (importante — estados diferentes).

```hcl
terraform {
  backend "s3" {
    bucket         = "meu-bucket-terraform-pedro-silveira"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

> Mesmo bucket S3 do dev, mas chave diferente (`prod/terraform.tfstate` vs `dev/terraform.tfstate`).
> O estado dos dois ambientes fica isolado.

---

### 2. `terraform/prod/variables.tf` — ATUALIZAR

Adicionar as variáveis que faltam:

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_account_id" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "django_secret_key" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type    = string
  default = "fintrack_db"
}

variable "db_username" {
  type    = string
  default = "fintrack_user"
}
```

> Remover `ecr_registry` — o ECR já existe e é criado uma vez só, o URL é calculado a partir do account_id.

---

### 3. `terraform/prod/main.tf` — REESCREVER

Esse é o arquivo principal. O atual só tem task definitions sem infra.
Você vai precisar criar tudo do zero, mas pode copiar grande parte do `dev/modules/infrastructure/main.tf` e adaptar.

**Diferenças chave em relação ao dev:**

#### a) Remover tudo relacionado ao DB ECS

Apagar:
- `aws_ecs_task_definition.db_task_prod`
- `aws_ecs_service.db_service`
- `aws_service_discovery_*` (não precisa mais)
- `aws_security_group.db_sg` (será substituído por `rds_sg`)

#### b) Adicionar subnets privadas para o RDS

```hcl
# Subnets privadas — sem rota para o IGW, RDS fica aqui
resource "aws_subnet" "prod_private_subnet" {
  count = 2

  vpc_id            = aws_vpc.prod_vpc.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name = "prod-private-subnet-${count.index}"
  }
}
```

> Subnets privadas **não têm** `map_public_ip_on_launch = true` e **não têm** route table com IGW.

#### c) Adicionar RDS subnet group

O RDS exige um subnet group com pelo menos 2 AZs:

```hcl
resource "aws_db_subnet_group" "prod_rds_subnet_group" {
  name       = "prod-rds-subnet-group"
  subnet_ids = aws_subnet.prod_private_subnet[*].id

  tags = {
    Name = "prod-rds-subnet-group"
  }
}
```

#### d) Adicionar security group para o RDS

```hcl
resource "aws_security_group" "rds_sg" {
  name        = "prod-rds-sg"
  description = "RDS aceita conexoes apenas do backend ECS"
  vpc_id      = aws_vpc.prod_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "prod-rds-sg"
  }
}
```

#### e) Adicionar a instância RDS

```hcl
resource "aws_db_instance" "prod_postgres" {
  identifier        = "fintrack-prod"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"      # ~$15/mês — mude para t3.small se precisar de mais RAM
  allocated_storage = 20                  # GB — mínimo para t3.micro

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.prod_rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible    = false          # nunca expor o banco na internet
  skip_final_snapshot    = false          # snapshot ao destruir (proteção de dados)
  final_snapshot_identifier = "fintrack-prod-final-snapshot"

  backup_retention_period = 7             # mantém backups por 7 dias
  backup_window           = "03:00-04:00" # UTC — janela de backup (madrugada BRT)
  maintenance_window      = "Mon:04:00-Mon:05:00"

  deletion_protection = true              # evita delete acidental via Terraform

  tags = {
    Name = "fintrack-prod-rds"
  }
}
```

> `deletion_protection = true` significa que `terraform destroy` vai falhar propositalmente no RDS.
> Para destruir, você precisa setar para `false` e aplicar antes.
> Isso é intencional — dado de produção não some por acidente.

#### f) Atualizar a task definition do backend

Trocar `DB_HOST` de `db-service.db.local` para o endpoint do RDS.
Adicionar `DJANGO_SECRET_KEY` e `DEBUG`:

```hcl
environment = [
  { name = "DB_NAME",          value = var.db_name },
  { name = "DB_USER",          value = var.db_username },
  { name = "DB_PASSWORD",      value = var.db_password },
  { name = "DB_HOST",          value = aws_db_instance.prod_postgres.address },  # ← chave da mudança
  { name = "DB_PORT",          value = "5432" },
  { name = "DJANGO_SECRET_KEY", value = var.django_secret_key },
  { name = "DEBUG",            value = "False" },
  { name = "ALLOWED_HOSTS",    value = "api.candlefarm.com.br" },
  { name = "CORS_ALLOWED_ORIGINS", value = "https://www.candlefarm.com.br" },
]
```

> `aws_db_instance.prod_postgres.address` resolve para o endpoint do RDS automaticamente.
> O Terraform sabe que a task definition depende do RDS e cria na ordem certa.

---

### 4. `terraform/prod/outputs.tf` — ATUALIZAR

O atual referencia recursos que não existem (`aws_lb.frontend_lb`, `aws_ecs_cluster.cluster`).
Atualizar para os nomes que você vai usar no `main.tf`:

```hcl
output "frontend_alb_dns" {
  description = "DNS do ALB do frontend"
  value       = aws_lb.frontend_lb.dns_name
}

output "backend_alb_dns" {
  description = "DNS do ALB do backend"
  value       = aws_lb.backend_lb.dns_name
}

output "rds_endpoint" {
  description = "Endpoint do RDS PostgreSQL"
  value       = aws_db_instance.prod_postgres.address
}

output "ecs_cluster_name" {
  description = "Nome do cluster ECS"
  value       = aws_ecs_cluster.prod_cluster.name
}
```

---

### 5. Backend Django — `backend/fintrack/fintrack/settings.py`

Três mudanças obrigatórias antes de ir para prod:

```python
# Antes (inseguro):
SECRET_KEY = 'django-insecure-...'
DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

# Depois (correto):
import os

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']     # quebra se não tiver — intencional
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_ALL_ORIGINS = False
```

> No container local (docker-compose), `DEBUG=True` e `DJANGO_SECRET_KEY` podem continuar
> sendo setados via `.env` — o código não muda, só o valor da variável de ambiente.

---

### 6. GitHub Actions — atualizar a pipeline

A pipeline `terraform_deploy_infra.yml` hoje hardcoda `dev-cluster` no step de force-redeploy:

```yaml
# Hoje — quebrado para prod:
aws ecs update-service --cluster dev-cluster --service backend-service ...

# Corrigir para usar o input de ambiente:
aws ecs update-service --cluster prod-cluster --service backend-service ...
```

Opções:
- Parametrizar o cluster name com base no `environment` input (melhor)
- Criar uma pipeline separada para prod

Também: o step `terraform apply` hoje só roda em `refs/heads/main`. Para prod isso é correto.

---

## Ordem de execução

Siga essa ordem na primeira vez:

```
1. Fazer as mudanças no settings.py do Django
2. Criar terraform/prod/backend.tf
3. Criar terraform/prod/prod.tfvars (não commitar)
4. Reescrever terraform/prod/main.tf com toda a infra
5. Atualizar terraform/prod/variables.tf e outputs.tf
6. Adicionar DJANGO_SECRET_KEY nos GitHub Secrets
7. Push para main
8. Rodar terraform_deploy_infra.yml com environment=prod
   → Cria: VPC, subnets, ECS, ALBs, SGs, RDS (leva ~8-12 min pelo RDS)
9. Rodar terraform_deploy_hosted_zone.yml com environment=prod
   → Cria: Route53 zone, records DNS
10. Rodar terraform_deploy_acm_https.yml com environment=prod
    → Cria: certificados ACM, listeners HTTPS
11. Verificar: acessar https://www.candlefarm.com.br
12. Rodar migrations manualmente (primeira vez):
    aws ecs run-task --cluster prod-cluster \
      --task-definition backend-task-prod \
      --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","migrate"]}]}'
```

---

## Custo estimado (us-east-1)

| Recurso | Tipo | $/mês |
|---------|------|-------|
| ECS Fargate frontend | 256 CPU / 512 MB, 24h/dia | ~$7 |
| ECS Fargate backend | 512 CPU / 1GB, 24h/dia | ~$14 |
| RDS PostgreSQL | db.t3.micro, 20GB | ~$15 |
| ALB frontend | 1 ALB | ~$16 |
| ALB backend | 1 ALB | ~$16 |
| **Total** | | **~$68/mês** |

> Para reduzir custo: usar Fargate Spot (70% desconto, mas containers podem ser interrompidos),
> ou desligar o RDS fora do horário de uso (só possível via script, não recomendado para prod real).

---

## Checklist final antes do go-live

- [ ] `SECRET_KEY` vem de variável de ambiente (não hardcoded)
- [ ] `DEBUG = False` em prod
- [ ] `CORS_ALLOWED_ORIGINS` restrito ao domínio
- [ ] `ALLOWED_HOSTS` configurado
- [ ] RDS com `publicly_accessible = false`
- [ ] RDS com `deletion_protection = true`
- [ ] RDS com `backup_retention_period >= 7`
- [ ] SG do RDS aceita tráfego apenas do `backend_sg`
- [ ] Migrations rodadas após primeiro deploy
- [ ] HTTPS funcionando (ACM + listeners 443)
- [ ] `terraform/prod/prod.tfvars` no `.gitignore`
