# Documentacao - CI/CD e Pipelines (Terraform + GitHub Actions)

## Visao Geral

Este projeto é totalmente automatizado por **quatro pipelines desacopladas** via **GitHub Actions**, seguras e modulares para provisionar infraestrutura na AWS, construir e publicar imagens Docker, configurar DNS e certificados HTTPS, e ainda destruir tudo quando necessário para evitar custos.

A execução pode ser feita diretamente via app mobile do GitHub, sem necessidade de terminal, VPN ou ambiente local. O provisionamento é seguro, modular e escalável.

## Estrutura dos Workflows

### 1. Pipeline de Deploy da Infraestrutura

- Executado via **GitHub Actions**, workflow manual (`workflow_dispatch`) com senha para segurança.
- Cria o **backend remoto (S3 + DynamoDB)** para controle de estado e concorrência.
- Provisiona **VPC**, **subnets**, **Security Groups**, **ECS Clusters**, **ALBs**, **Target Groups**, **roles IAM**, **RDS** e **repositórios ECR**.
- Utiliza `terraform init`, `plan` e `apply` com arquivos `.tfvars` por ambiente.

- Define dependências claras entre recursos (ex: ALBs só são criados após subnets e IGW).

- ### 1.1. Build e Push das Imagens Docker

  - Executado após a infraestrutura estar provisionada.
  - Utiliza Docker Buildx para build multiplataforma (linux/amd64).
  - Faz login no Amazon ECR.
  - Builda e envia as imagens Docker do backend e frontend para os repositórios ECR.

> Recursos duplicados ou reaplicados quebram a pipeline, pois o Terraform detecta que já existem e recusa recriar, garantindo **segurança e controle de custo**.

---

### 2. Pipeline de DNS (Hosted Zone via Route 53)

- Executado após a infraestrutura principal.
- Cria a **zona DNS pública**  no **Route53** para o domínio principal (ex: `candlefarm.com.br`).
- Cria registros tipo `A` para `www.` (frontend) e `api.` (backend).
- Aponta para os DNS dos ALBs criados na etapa anterior.
- Atualiza os `NameServers` como output para serem copiados ao painel GoDaddy (ou outro registrador).

---

### 3. Pipeline de Certificados ACM (HTTPS)

- Executado após a Hosted Zone, acima.
- Provisiona certificado SSL/TLS com **AWS Certificate Manager (ACM)**, para `www.candlefarm.com.br` e `api.candlefarm.com.br`.
- Valida automaticamente via DNS usando registros adicionados via Terraform
- Associa os certificados aos **listeners HTTPS (porta 443)** dos ALBs

> Toda a comunicação externa passa a ser feita com segurança via HTTPS.

---

### 4. Pipeline de Destruição (Destroy)

- Também executado manualmente com senha.
- Executa `terraform destroy` para todos os módulos
- Deleta todos os recursos provisionados: ALBs, ECS, RDS, Route 53, ACM, etc.
- **Remove o backend remoto** (S3 + DynamoDB) no final
- Não sobra nenhum recurso na AWS: **zero billing residual**
- Pode ser executado com senha de proteção via `workflow_dispatch`

> Em menos de **5 minutos**, todo o ambiente é destruído com segurança e rastreabilidade.

## Organização e Segurança

- As pipelines usam variáveis de ambiente com segredos do GitHub (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc).
- A execução manual exige senha para evitar execuções acidentais ou não autorizadas.
- O estado do Terraform é armazenado remotamente no S3 e DynamoDB, garantindo:
  - Controle de concorrência e bloqueios
  - Histórico e rastreabilidade de mudanças
- Os recursos são separados por módulos e ambientes (`dev`, `staging`, `prod`) usando arquivos `.tfvars`.


## Beneficios

- Executado de qualquer lugar via GitHub Actions
- Estado versionado e concorrente com S3 + DynamoDB
- Totalmente modular e desacoplado
- Validação HTTPS automática com Route 53 + ACM
- Infraestrutura segura, rastreável e reaplicável por qualquer membro da equipe


# Configuração do Domínio e Considerações sobre Deleções Manuais

## Passo: Configurar os Name Servers no GoDaddy

Após a criação da **Hosted Zone** na AWS Route53 (via Terraform na pipeline), a AWS gera um conjunto de **Name Servers (NS)** exclusivos para sua zona DNS. 

### O que fazer:

1. **Acesse o painel do seu registrador de domínio** (exemplo: GoDaddy).
2. Localize a configuração de DNS para o domínio em questão.
3. Substitua os servidores DNS atuais pelos **Name Servers gerados na Hosted Zone da AWS**.
   - Essa informação é obtida via saída do Terraform (`terraform output`) ou diretamente no console AWS Route53.
4. Salve as alterações.

### Importante:

- A propagação dessas mudanças pode levar até 48 horas, mas normalmente é bem mais rápida (algumas horas).
- Durante esse período, o domínio começará a apontar para os Load Balancers provisionados na AWS, e o acesso ao site ficará disponível conforme a infraestrutura criada.

---

## Impacto de Deletar Recursos Manualmente na AWS

### O que acontece se um recurso for removido manualmente (fora do Terraform)?

- **Estado do Terraform fica inconsistente:** o Terraform mantém um arquivo de estado (`terraform.tfstate`) que "conhece" os recursos provisionados.
- Se você apagar um recurso manualmente, o Terraform ainda "acha" que ele existe no estado.
- Ao rodar alguma pipeline como a de destroy por exemplo, podem ocorrer erros porque o recurso esperado não existe mais.
- Dependendo do recurso e dependências, isso pode causar:
  - **Falhas na pipeline** porque o Terraform tenta gerenciar algo inexistente.
  - **Recursos órfãos**, que ficam na AWS sem controle pelo Terraform.
  - Problemas de segurança, custo e manutenção.

### Boas práticas para deletar recursos:

- Use a pipeline de **destroy** que já está configurada para limpar tudo com segurança e controle, deleções manuais no console podem impactar o funcionamento normal das pipelines.

---

## Resumo

- Configurar os Name Servers no GoDaddy é fundamental para que o domínio funcione apontando para a AWS.
- Deletar recursos manualmente na AWS pode quebrar seu controle de infraestrutura e causar falhas na pipeline.
- Use sempre o Terraform para alterações e destruição para manter o ambiente consistente, seguro e fácil de manter.

**Proximo:** `docs/3_arquitetura_aplicacao.md`

