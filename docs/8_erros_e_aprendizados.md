# Erros Comuns e Aprendizados - Projeto Cloud AWS com React, Django, Terraform e Nginx

Este documento registra os principais erros enfrentados, decisões importantes e aprendizados ao longo do desenvolvimento e deploy da infraestrutura, com foco em produção real usando ECS, Terraform e CI/CD.

---

## 1. Erro: Injeção de variáveis no build do Docker (React)

### Problema

Durante o build da imagem Docker do frontend, tentava-se usar a variável `REACT_APP_BACKEND_URL` para embutir no React **durante o build**:

```dockerfile
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
RUN npm run build
```

Porém, o valor dessa variável era baseado no Load Balancer do backend, que só existe **depois da infraestrutura** estar criada (runtime).

### Solução

Usar `envsubst` para substituir dinamicamente no `nginx.conf.template`, **em runtime**, dentro do container.

```dockerfile
COPY nginx.conf /etc/nginx/templates/nginx.conf.template
RUN envsubst '${REACT_APP_BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf
```

---

## 2. Erro: `invalid URL prefix` no nginx.conf

### Problema

O erro:

```
[emerg] 1#1: invalid URL prefix in /etc/nginx/conf.d/default.conf:19
```

ocorreu porque o `nginx.conf` tinha:

```nginx
proxy_pass ${REACT_APP_BACKEND_URL}/api/;
```

mas a variável não foi substituída corretamente, pois a substituição foi feita no `Dockerfile` **antes da variável existir**.

### Solução

Passar a variável no ECS Task Definition e realizar substituição no entrypoint.

---

## 3. Timeout nos ALBs e conexões grandes

### Problema

Ao tentar fazer upload de arquivos grandes (~~150MB), tomava-se `ERR_CONNECTION_RESET` ou `502 Bad Gateway` após 60~~160 segundos.

### Solução

* Aumentar o `idle_timeout` do ALB para 300s
* Ajustar buffers no Nginx:

```nginx
client_max_body_size 150M;
proxy_request_buffering off;
client_body_buffer_size 128M;
proxy_buffers 16 64k;
proxy_busy_buffers_size 128k;
```

> Observação: Em instâncias ECS pequenas (256 CPU / 512 MB), desativar `proxy_request_buffering` pode causar crash do container por falta de RAM.

---

## 4. Nginx ignorando prefixo `/api` no backend

### Problema

Mesmo com `location /api/`, o backend ainda estava servindo toda aplicação em `/`, causando 405/404.

### Solução

Garantir que o Nginx do **frontend** faz `proxy_pass` corretamente para:

```nginx
location /api/ {
    proxy_pass http://backend-lb/api/;
}
```

E o backend deve tratar `/api/` como seu path base.

---

## 5. ECS Task `unhealthy` e falhas nos health checks

### Problema

O container caía repetidamente e não ficava `healthy` no ALB, principalmente após ajuste de configurações pesadas no Nginx (buffers).

### Solução

* Garantir que a porta correta está exposta (8000 no backend)
* Health check com `path = /api/health/`
* Instância mais robusta no backend: `512 CPU / 1024 MB`

---

## 6. Segurança interna vs externa (HTTPS x HTTP)

### Problema

Havia dúvida sobre se o `REACT_APP_BACKEND_URL` deveria usar HTTP ou HTTPS.

### Conclusão

* Dentro da mesma VPC, comunicação pode ser HTTP
* Se o frontend expõe APIs para uso externo, backend precisa estar acessível via HTTPS
* Listeners do ALB configurados para 443 (HTTPS) com ACM

---

## 7. Falta de robustez no deploy manual

### Problema

Inicialmente se executava `terraform apply` manualmente para cada etapa

### Solução

Criar pipelines GitHub Actions em etapas:

1. Deploy da infraestrutura
2. Deploy da hosted zone + certificados
3. Build das imagens + push no ECR
4. Pipeline de destroy segura, que remove até o backend remoto

---

## 8. Variável de ambiente no ECS vs no Docker

### Problema

Confusão entre o momento da variável ser usada:

* Build do Docker: não conhece valor da infra
* Execução do container (runtime): ECS sabe do valor

### Solução

* Não usar `REACT_APP_BACKEND_URL` em `npm run build`
* Usar somente para Nginx em runtime, via `envsubst`

---

## 9. Uploads grandes: limitar buffering por hardware

Em instâncias pequenas (256 CPU / 512MB), desativar buffering pode causar crash. Ajustes:

```nginx
client_max_body_size 150M;
client_body_buffer_size 8M;
proxy_buffers 8 16k;
proxy_busy_buffers_size 32k;
```

Substituir uploads gigantes por S3 com presigned URL caso necessário.

---

## 10. Aprendizados Gerais

* Separar *build-time* e *runtime* é crucial
* Variáveis no Docker devem ser tratadas com cuidado (ex: `ARG` não é `ENV`)
* ECS Fargate tem limites de memória reais (cuidado com o frontend fazendo proxy)
* ALBs precisam de `idle_timeout` maior para uploads grandes
* `proxy_pass` no Nginx não pode ter barra final se quiser manter path correto
* Health checks mal configurados impedem ECS de funcionar
* É vital testar **fim a fim** com arquivos reais, não apenas simulação

---

Esse documento deve ser mantido e expandido conforme novos erros e soluções forem surgindo.
