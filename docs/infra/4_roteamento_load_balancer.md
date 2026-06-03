# Documentacao - Roteamento com Load Balancer (Frontend e Backend)

## Visao Geral

O roteamento entre frontend e backend neste projeto é realizado por dois **Application Load Balancers (ALBs)** distintos, ambos configurados via Terraform. O frontend e backend possuem seus próprios ECS Services e target groups, e a comunicação ocorre via proxy do Nginx (no frontend) para o ALB do backend.

Toda comunicação interna entre os componentes ocorre dentro da mesma VPC, utilizando nomes DNS privados e segurança provida por grupos de segurança (Security Groups).

---

## Estrutura de Roteamento

```
Usuário (browser)
  ↓
ALB do Frontend (porta 80/443)
  ↓
ECS Task do Frontend com Nginx
  ↓
Nginx intercepta /api/* e redireciona para:
  ↓
ALB do Backend (via DNS interno ou externo)
  ↓
ECS Task do Backend com Nginx
  ↓
Gunicorn (via UNIX socket) → Django
```

---

## Configuração dos ALBs via Terraform

Cada Load Balancer é configurado com:
- `load_balancer_type = "application"`
- `idle_timeout = 300` para suportar uploads grandes
- `enable_cross_zone_load_balancing = true`
- Listeners nas portas 80 e 443
- Target Groups associados aos ECS Services

```hcl
resource "aws_lb_listener" "frontend_http_listener" {
  load_balancer_arn = aws_lb.frontend_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
  }
}
```

---

## Comunicação entre os Containers

- A URL configurada na variável `REACT_APP_BACKEND_URL` aponta para o DNS do ALB do backend.
- Essa URL é utilizada pelo Nginx do frontend como valor de `proxy_pass`.
- Exemplo de configuração:

```nginx
location /api/ {
    proxy_pass ${REACT_APP_BACKEND_URL}/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## Considerações de HTTPS

- Os certificados HTTPS são aplicados diretamente nos **ALBs** com suporte a ACM
- O Nginx dos containers não faz SSL termination; isso é feito no ALB
- Dessa forma, os containers continuam operando em HTTP, mas a comunicação externa é segura

---

## Configuração dos Target Groups

- Frontend: escuta porta 80
- Backend: escuta porta 8000
- Health checks configurados para:
  - `/` (frontend)
  - `/api/health/` (backend)

---

## Benefícios

- Isolamento completo entre frontend e backend
- Roteamento claro e escalável
- Certificados HTTPS gerenciados com ACM
- Monitoramento e health checks integrados

**Próximo:** `docs/5_seguranca_https.md`

