# Documentacao - Seguranca e HTTPS

## Visao Geral

A aplicacao adota boas praticas de seguranca com uso de certificados TLS, roteamento interno protegido, isolamento por VPC e controle de trafego por Security Groups. O objetivo e garantir que apenas comunicacoes autorizadas e seguras ocorram entre os componentes do sistema.

---

## Certificados HTTPS com ACM

- Utiliza o **AWS Certificate Manager (ACM)** para gerenciar certificados SSL.
- Os certificados sao vinculados diretamente aos **Load Balancers (ALBs)**.
- O trafego externo usa **HTTPS** (porta 443), enquanto o trafego interno entre containers permanece em **HTTP**, dentro da VPC segura.

### Provisionamento dos Certificados:

1. Criacao automatica via Terraform (pipeline `certificates`) com validacao DNS
2. Associacao dos certificados com os ALBs nos listeners HTTPS

```hcl
resource "aws_lb_listener" "frontend_https_listener" {
  load_balancer_arn = aws_lb.frontend_lb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = module.hosted_zone_acm.frontend_cert_ext.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
  }
}
```

---

## Roteamento Seguro com VPC e SGs

- Toda comunicacao entre frontend e backend ocorre dentro da **mesma VPC**, garantindo isolamento.
- Os **Security Groups** garantem que:
  - O frontend so pode acessar o backend via ALB
  - Nenhum servico ECS e acessivel diretamente da internet
  - Apenas os ALBs expostos publicamente recebem trafego externo

---

## HTTPS vs HTTP nas Variaveis de Ambiente

### Comunicacao Interna:

- Feita via HTTP entre containers (dentro da VPC)
- Exemplo:

```hcl
environment = [
  {
    name  = "REACT_APP_BACKEND_URL"
    value = "http://${aws_lb.backend_lb.dns_name}"
  }
]
```

- Justificado porque o trafego nao sai da AWS e esta protegido

### Comunicacao Externa (Publica):

- O acesso ao site (frontend) e API (backend) pela internet e feito via HTTPS, garantindo seguranca ao usuario

---

## Observacoes Finais

- O Nginx nao realiza terminacao SSL; isso e responsabilidade do ALB
- O uso de ACM simplifica a renovacao e gestao dos certificados
- O certificado cobre os subdominios:
  - `www.candlefarm.com.br` (frontend)
  - `api.candlefarm.com.br` (backend, se exposto publicamente)


  ## Camadas, Conexões e AWS Detalhada (VPC, SGs, Target Groups)

### Passo a Passo Completo do Fluxo:

1. **Usuário (Navegador)** acessa o site via `http://frontend-alb`
2. A requisição entra no **Load Balancer do Frontend**, que:
   - Escuta vis listeners nas portas **80 e 443** (HTTP e HTTPS separados)
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
   - Escuta nas portas **80 e 443** (HTTP e HTTPS separados)
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

**Proximo:** `docs/6_draw_io.md`

