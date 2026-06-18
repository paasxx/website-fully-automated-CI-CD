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

---

## 11. Pipeline falha no `build_and_push` — não precisa destruir tudo

### Problema

A pipeline `Deploy Infrastructure` tem 4 jobs em sequência:
1. `create_s3_and_dynamodb` → bootstrap do estado Terraform
2. `terraform` → provisiona VPC, ECS, ALB, ECR, etc.
3. `print_terraform_outputs_and_state` → loga outputs
4. `build_and_push` → builda imagens Docker e envia ao ECR

Se o job `build_and_push` falhar (ex: dependência faltando no `package.json`), os recursos AWS **já foram criados** pelos jobs anteriores. A tendência é querer destruir tudo e recomeçar — mas isso é desnecessário e lento.

### Solução

O Terraform é **idempotente**: rodar `terraform apply` numa infra que já existe resulta em zero mudanças. Basta:

1. Corrigir o código que causou a falha
2. Fazer push da correção
3. Disparar uma nova run do `workflow_dispatch` (não usar "Re-run failed jobs" — veja item 12)

Na nova run, os steps de Terraform concluem em segundos (nada a criar), e o `build_and_push` roda com o fix.

---

## 12. "Re-run failed jobs" não pega commits novos

### Problema

Ao clicar em "Re-run failed jobs" no GitHub Actions, o comportamento esperado é que a pipeline rode com o código mais recente — mas não é isso que acontece.

### Como funciona de verdade

"Re-run failed jobs" reabre os jobs com o **mesmo commit SHA** da run original. Qualquer push feito depois daquele commit é ignorado.

### Solução

Para incluir um fix num job que falhou, é necessário **disparar uma nova run**:

- Actions → Deploy Infrastructure → **Run workflow** → selecionar a branch → preencher inputs → Run

---

## 13. `Terraform Apply` só roda na branch `main` — feature branches pulam esse step

### Como está configurado

```yaml
- name: Terraform Apply
  if: github.ref == 'refs/heads/main'
```

Isso significa que ao rodar o `workflow_dispatch` a partir de uma feature branch:
- Os steps de `terraform init`, `plan` e outputs rodam normalmente
- O `terraform apply` é **pulado** automaticamente
- O job `build_and_push` **continua rodando** — não tem restrição de branch

### Quando isso é útil

Se a infra já existe e você só quer atualizar as imagens Docker (ex: corrigir um bug no frontend), pode rodar a pipeline direto da feature branch sem risco de alterar a infraestrutura. O Terraform plan vai mostrar zero mudanças, o Apply é pulado, e as imagens são buildadas e enviadas ao ECR normalmente.

### Regra geral

| Situação | Rodar de |
|---|---|
| Primeira criação da infra | `main` |
| Mudança de infra (Terraform) | `main` |
| Só atualizar imagens (código) | feature branch ou `main` |
| Teste rápido após bug no build | feature branch |

---

## 14. Nomenclatura: "dev" no input da pipeline ≠ `Dockerfile.dev`

### Problema

A pipeline pede um input `environment` com default `dev`. Ao mesmo tempo, existia um `Dockerfile.dev` no repositório. Isso criava confusão: parecia que rodar com `environment: dev` usaria o `Dockerfile.dev`.

### Como realmente funciona

| Nome | Significado |
|---|---|
| `environment: dev` (input da pipeline) | **Ambiente AWS** — aponta para `terraform/dev/` e suas variáveis |
| `Dockerfile.local` | **Imagem de desenvolvimento local** — usa `tail -f /dev/null`, hot reload, sem build |
| `Dockerfile.prod` | **Imagem deployável** — multi-stage build, compila o React, serve via Nginx + Gunicorn |

A pipeline **sempre** usa `Dockerfile.prod` para os dois serviços, independente do ambiente escolhido. O que muda entre `dev`, `staging` e `prod` é a infraestrutura Terraform (tamanho das instâncias, variáveis de banco, etc.), não a imagem Docker.

### Solução aplicada

`Dockerfile.dev` foi renomeado para `Dockerfile.local` em todo o repositório (arquivos físicos + docker-compose + docs).

---

## 15. Peer dependency não declarada quebra o build de produção silenciosamente

### Problema

A biblioteca `react-timezone-select` depende de `react-select` como peer dependency. Localmente, `npm install --legacy-peer-deps` instala sem erro e a aplicação funciona. Na pipeline, o build falhou com:

```
[vite]: Rollup failed to resolve import "react-select" from "react-timezone-select/dist/index.js"
```

### Por que só falha na pipeline

Localmente, o `node_modules` pode ter o `react-select` instalado indiretamente por outra lib. Na pipeline, o Docker faz um `npm install` limpo a partir do `package.json` — e o que não está declarado, não é instalado.

### Solução

Sempre declarar explicitamente todas as peer dependencies no `package.json`, mesmo que `npm install` não reclame:

```json
"react-select": "^5.8.0",
"react-timezone-select": "^3.3.3"
```

### Regra geral

Se uma biblioteca exige outra no `peerDependencies`, declare as duas no seu `package.json`. O `--legacy-peer-deps` mascara o problema localmente mas não resolve na CI.
