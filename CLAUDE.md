# Guia do Projeto — Personal Finance Dashboard

Documento de orientação rápida para retomar o projeto depois de uma pausa.
Leia isso antes de abrir qualquer arquivo de código.

---

## O que é este projeto

Dashboard pessoal de finanças. O usuário faz upload das faturas do cartão de crédito
(Nubank, Inter, BTG em CSV) e vê: gastos por categoria, evolução mensal, top merchants.

Produto pessoal que pode escalar para multi-tenant/corporativo — o schema foi projetado
com isso em mente (particionamento, RLS).

---

## Stack

| Camada   | Tecnologia                               |
| -------- | ---------------------------------------- |
| Frontend | React 18 + Vite 5 + SCSS                 |
| Backend  | Django 4.2 + DRF + Gunicorn              |
| Banco    | PostgreSQL 16 (particionado por mês)     |
| Infra    | AWS ECS Fargate + ALB + ECR + RDS        |
| IaC      | Terraform (estado remoto: S3 + DynamoDB) |
| CI/CD    | GitHub Actions (4 pipelines)             |
| Local    | Docker Compose + Makefile                |

---

## Como rodar localmente

```bash
make dev          # sobe containers + migra + inicia back e front
make logs         # todos os logs
make logs-back    # só backend
make logs-front   # só frontend
make shell-back   # entra no container Django
make migrate      # makemigrations + migrate
make help         # lista todos os comandos
```

Frontend: http://localhost:3000
Backend: http://localhost:8000

---

## Estrutura de pastas importante

```
backend/fintrack/         # projeto Django (em migração para DDD)
  ├── core/               # settings, configurações globais (a criar)
  ├── identity/           # auth: User, JWT (a criar)
  ├── importacao/         # parsing de faturas CSV (a criar)
  ├── financas/           # Transacao (particionada), Categoria (a criar)
  └── analytics/          # aggregations, materialized views (a criar)

frontend/front/src/
  ├── api/                # axiosConfig.js (instância axios com CSRF)
  ├── components/
  │   ├── Dashboard/      # cards do dashboard (WIP)
  │   ├── Navbar/         # navbar + theme toggle
  │   └── Legacy/         # componentes antigos — REMOVER em breve
  ├── context/
  │   ├── ThemeContext    # dark/light mode (funcionando)
  │   └── FileContext     # lista de arquivos com mock — substituir por API real
  ├── pages/              # Home, Login (placeholder), Profile (placeholder)
  └── styles/
      ├── global/         # Variables.scss, Mixins.scss, Reset.scss
      └── components/     # um arquivo por componente

terraform/
  ├── bootstrap-backend/  # cria S3 + DynamoDB (roda primeiro)
  └── dev/
      ├── modules/
      │   ├── infrastructure/    # VPC, ECS, ALBs, ECR, SGs, IAM
      │   └── hosted_zone_acm/  # Route53, ACM, listeners HTTPS
      └── backend.tf    # aponta para o S3 do bootstrap
```

---

## Estado atual (junho 2026)

### Funcionando

- [x] Infraestrutura AWS completa (deploy + destroy via pipeline)
- [x] Ambiente local com Docker Compose
- [x] Frontend Vite rodando com React Router e dark/light theme
- [x] Backend Django com endpoint de health check
- [x] Makefile com comandos do dia a dia

### Em construção

- [ ] Autenticação (JWT) — backend sem auth ainda
- [ ] Modelos do domínio financeiro (Transacao, Categoria, Fatura)
- [ ] Parser de faturas Nubank/Inter/BTG
- [ ] Dashboard com dados reais
- [ ] Login page (só placeholder)

### Débitos técnicos conhecidos

- `SECRET_KEY` hardcoded em settings.py → deve vir de env var
- `DEBUG = True` em settings.py → deve ser `False` em prod
- `CORS_ALLOW_ALL_ORIGINS = True` → restringir por origem em prod
- Legacy components em `src/components/Legacy/` → remover
- FileContext com mock data → conectar à API real
- `prod/` no Terraform está incompleto (só task definitions, sem infra)

---

## Decisões de arquitetura

**Banco de dados em ECS (não RDS)**
O banco roda como container ECS Fargate com service discovery (`db-service.db.local`).
É ephemeral por design para dev/testes — dados são perdidos se o container reiniciar.
Para produção, migrar para RDS PostgreSQL 16.

**Particionamento no PostgreSQL**
A tabela `Transacao` será particionada por `RANGE (data)`, uma partição por mês.
Justificativa: queries financeiras são quase sempre time-bounded. Permite partition pruning.
Escalabilidade: adicionar Row Level Security por `user_id` para multi-tenant.

**Dois ALBs independentes**
Frontend ALB e Backend ALB separados permitem escalar cada serviço independentemente.
O frontend Nginx faz proxy de `/api/` para o ALB do backend (não acesso direto ao ECS).

**Variáveis de ambiente React em runtime**
`REACT_APP_BACKEND_URL` é injetada via `envsubst` no nginx.conf em runtime (não no build).
Isso permite a mesma imagem Docker servir dev/staging/prod com valores diferentes.

**Vite em vez de Create React App**
CRA foi arquivado em 2023 e tem conflitos crescentes com npm/Node modernos.
Vite 5 tem build 10x mais rápido, zero conflitos de peer deps, suporte nativo a SCSS.

---

## Domínios DDD (design planejado)

```
identity/     → User, autenticação, autorização
importacao/   → Fatura (arquivo bruto), ImportacaoLog, parsers por banco
financas/     → Transacao (particionada), Categoria, RegraCategorizacao
analytics/    → aggregations, materialized views, endpoints do dashboard
```

Cada domínio é um Django app separado com seus próprios models, views, urls e services.
Não cruzar domínios diretamente — usar signals ou services na camada de aplicação.

---

## Formatos de fatura conhecidos

| Banco  | Formato | Separador | Encoding |
| ------ | ------- | --------- | -------- |
| Nubank | CSV     | `,`       | UTF-8    |
| Inter  | CSV     | `;`       | UTF-8    |
| BTG    | CSV     | `,`       | UTF-8    |

Sempre validar encoding antes de parsear (faturas com caracteres especiais podem vir em latin-1).

---

## Pipelines GitHub Actions

| Pipeline                           | Quando usar                                 |
| ---------------------------------- | ------------------------------------------- |
| `terraform_deploy_infra.yml`       | Primeira vez ou mudança de infra            |
| `terraform_deploy_hosted_zone.yml` | Após infra, para criar DNS                  |
| `terraform_deploy_acm_https.yml`   | Após hosted zone, para HTTPS                |
| `terraform_destroy.yml`            | Para destruir TUDO incluindo backend remoto |
| `run_tests.yml`                    | PR para main                                |

Todas as pipelines de infra exigem senha (secret `WORKFLOW_PASSWORD`).
Sempre destruir após testes para não gerar custo na AWS.

---

## Variáveis de ambiente necessárias (GitHub Secrets)

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_ACCOUNT_ID
WORKFLOW_PASSWORD      # senha para acionar pipelines manualmente
DB_PASSWORD            # senha do banco de dados
DJANGO_SECRET_KEY      # chave secreta do Django (não commitar)
```
