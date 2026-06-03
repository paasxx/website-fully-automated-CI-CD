##  Diagrama

O diagrama da arquitetura completa pode ser visualizado com base nas conexões descritas acima. Você pode utilizar o [draw.io](https://app.diagrams.net/) e seguir o seguinte guia:

* Comece com `S3` e `DynamoDB` no topo
* Conecte com `Terraform` simbolizando o backend remoto
* Crie dois caminhos para ALB do frontend e backend
* Conecte os ALBs com ECS Services
* Adicione `RDS` para o backend
* Coloque o `Route53` com apontamentos DNS e ACM

---

Essa documentação cobre todos os recursos, conexões e arquitetura da infraestrutura provisionada com Terraform na AWS. Ideal para consulta pessoal ou colaboração em equipe.
