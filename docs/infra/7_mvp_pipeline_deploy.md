## Pipelines de deploy da infraestrutura

O projeto usa **3 workflows separados** no GitHub Actions (`.github/workflows/`), cada um disparado
manualmente (`workflow_dispatch`), com um `environment` (dev/prod) e uma senha checada contra
`secrets.WORKFLOW_PASSWORD`. Existe também `terraform_destroy.yml`, o inverso de cada um deles.

```
terraform_deploy_infra.yml        → VPC, ECS, ALBs, SGs (módulo infrastructure) + build/push das imagens
terraform_deploy_hosted_zone.yml  → Route53 (módulo hosted_zone_acm) — depende da infra já existir
terraform_deploy_acm_https.yml    → certificados ACM + listeners HTTPS — depende da hosted zone
terraform_destroy.yml             → desfaz os três, na ordem inversa
```

### 1. `terraform_deploy_infra.yml`

- **`create_s3_and_dynamodb`**: cria o backend remoto (bucket S3 + tabela DynamoDB de lock) — só
  na primeira vez; um step anterior checa se já existe e pula se sim.
- **`terraform`**: `init` + `plan` + `apply` do módulo `infrastructure` (o `apply` só roda em `main`).
- **`print_terraform_outputs_and_state`**: lista os outputs e o state, só pra log.
- **`build_and_push`**: builda as imagens Docker (`Dockerfile.prod` de front e back), sobe pro ECR,
  força o ECS a redeployar com a imagem nova.

### 2. `terraform_deploy_hosted_zone.yml`

`init` + `plan` + `apply` do módulo `hosted_zone_acm`, direcionado (`-target`) só nos recursos de
Route53 (zone + records). Roda depois da infra existir, porque precisa do DNS dos ALBs.

### 3. `terraform_deploy_acm_https.yml`

Mesma lógica, `-target=module.hosted_zone_acm`, mas cobrindo os certificados ACM e os listeners
HTTPS — depende da hosted zone já estar criada.

### Nenhuma delas usa `-var-file`

Os valores sensíveis (`db_password`, `aws_account_id`, `django_secret_key`) nunca ficam em arquivo
— vêm direto dos GitHub Secrets, passados como `-var` na própria chamada do terraform:

```yaml
- name: Terraform Apply
  run: terraform apply -auto-approve \
    -var="db_password=${{ secrets.DB_PASSWORD }}" \
    -var="aws_account_id=${{ secrets.AWS_ACCOUNT_ID }}" \
    -var="django_secret_key=${{ secrets.DJANGO_SECRET_KEY }}" \
    -target=module.infrastructure
  working-directory: ./terraform/${{ github.event.inputs.environment }}
```

`terraform init` não precisa de `-var` nenhum (não avalia variáveis, só configura backend/providers).

### Ordem de execução (primeira vez, ou depois de um destroy)

1. `terraform_deploy_infra.yml`
2. `terraform_deploy_hosted_zone.yml`
3. `terraform_deploy_acm_https.yml`

Pra destruir, `terraform_destroy.yml` na ordem inversa.

> Detalhes de como reconstruir isso do zero para `prod` (RDS, subnets privadas, etc.) estão em
> `terraform/PROD_RDS_HOWTO.md`.
