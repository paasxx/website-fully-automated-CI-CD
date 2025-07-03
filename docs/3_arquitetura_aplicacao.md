# Documentacao - Arquitetura da Aplicacao (React + Django + Nginx + ECS)

## Visao Geral

A arquitetura do projeto segue um modelo desacoplado com **dois containers isolados**: um frontend em React e um backend em Django. Cada container é exposto por um Load Balancer distinto, e cada componente roda em um serviço ECS Fargate diferente. A comunicação interna é feita via Nginx e o roteamento entre containers é garantido por ALBs configurados via Terraform.

## Componentes Principais

### Frontend

- **Tecnologia**: React
- **Servidor Web**: Nginx
- **Hospedagem**: ECS Fargate
- **Roteamento**: Load Balancer com listener HTTP (porta 80) e listener HTTPS (porta 443)
- **Comunicação com o backend**: via proxy\_pass para o ALB do backend usando path `/api/`
- **Variável de Ambiente**: `REACT_APP_BACKEND_URL` apontando para o ALB do backend
- **Deploy**: imagem Docker hospedada no Amazon ECR

### Backend

- **Tecnologia**: Django + Gunicorn
- **Servidor Web**: Nginx
- **Hospedagem**: ECS Fargate
- **Banco de Dados**: RDS PostgreSQL privado
- **Exposição**: Load Balancer com listener HTTP (porta 80)
- **Requisições internas**: via proxy\_pass do frontend
- **Deploy**: imagem Docker hospedada no Amazon ECR

---
## Backend URL

O backend é configurado dinamicamente com:

```hcl
# Terraform (frontend ECS Task)
environment = [
  {
    name  = "REACT_APP_BACKEND_URL"
    value = "http://${aws_lb.backend_lb.dns_name}"
  }
]
```
Essa variável é usada no build do React e também no template `nginx.conf.template`.


### Load Balancers (ALBs)

- Um ALB para o frontend
  - Listener HTTP 80 e opcionalmente HTTPS 443
  - Aponta para o Target Group do ECS do frontend (porta 80)
- Um ALB para o backend
  - Listener HTTP 80 e opcionalmente HTTPS 443
  - Aponta para o Target Group do ECS do backend (porta 8000)

## Fluxo da Requisição

```
[Usuário (Navegador)]
   |
   v
[Load Balancer do Frontend (porta 80 e 443)]
   |
   v
[Container do Frontend (porta 80 com Nginx)
   | (via proxy_pass no Nginx frontend para /api)]
   v
[Load Balancer do Backend (porta 80 e 443)]
   |
   v
[Container do Backend (porta 8000 com Gunicorn e Nginx)]
   |
   v
[Django]
```

## Segurança

- Toda comunicação entre containers ocorre dentro da mesma **VPC**, considerada segura
- Nginx do frontend se comunica com o backend via HTTP pois trafega internamente
- A comunicação externa com o frontend ou backend pode ser HTTPS via certificados ACM

##  React - funcionamento geral

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


## Proxy com Nginx no Frontend

- Escuta na porta **80**
- As chamadas feitas pelo React usam `baseURL: '/api'`
- `location /` → serve o React build (index.html e estáticos)
- `location /api/` → faz proxy_pass para o backend-alb (respeitando `/api` no caminho)
- `client_max_body_size` ajustado para permitir uploads grandes
- Barra no `proxy_pass` deve ser evitada para manter `/api/...` corretamente


Exemplo de trecho relevante no `nginx.conf`:

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
        proxy_pass ${REACT_APP_BACKEND_URL}/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        client_max_body_size 150M;
    }
}
```

##  Dockerfile do Frontend 

```Dockerfile
FROM node:16 as builder

WORKDIR /app
COPY front/ /app

RUN npm install --silent
RUN npm install axios --silent
RUN npm rebuild node-sass --silent

# Build do React
RUN npm run build

# Etapa 2: Nginx + substituição da conf
FROM nginx:latest

# Instala envsubst
RUN apt-get update && apt-get install -y gettext-base

# Copia e prepara template do nginx.conf
COPY nginx.conf /etc/nginx/templates/nginx.conf.template

# Copia build do React
COPY --from=builder /app/build /usr/share/nginx/html

# Inicia nginx
CMD ["/bin/sh", "-c", "envsubst '${REACT_APP_BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]

```

#### Importante: A variável REACT_APP_BACKEND_URL tem que ser atribuida dentro do comando CMD que é rodado após o build do dockerfile, pois essa variável está disponível somente dentro dos containers no ECS (ver terraform main.tf do módulo infrastructure) e não em tempo de build no ECR.


## Proxy com Nginx no Backend

- Escuta na porta **8000**
- `location /api/` → proxy para Gunicorn (via socket)
- `location /static/` e `/media/` → servem arquivos diretamente
- Também ajustado com `client_max_body_size`

```nginx
location /api/ {
    proxy_pass http://gunicorn;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```


## Considerações Finais

- Toda requisição do React passa pelo Load Balancer do frontend.
- O Nginx do frontend roteia para o backend, usando `/api/` como prefixo.
- O Terraform injeta dinamicamente o endereço correto do Load Balancer do backend.
- O Dockerfile e o Nginx são configurados para aceitar uploads grandes e realizar substituições com `envsubst`.
- Todas as permissões entre ALBs, containers e banco são controladas por **Security Groups** de forma clara e segura.
- O uso correto das portas (80/443, 8000) e `proxy_pass` com/sem barra é fundamental para o roteamento funcionar.
- A separação por ALB para cada serviço e os respectivos Target Groups garante isolamento e facilita futura escalabilidade.
- A VPC organiza todos os recursos em uma infraestrutura segura e controlada.

**Próximo:** `docs/4_roteamento_load_balancer.md`

