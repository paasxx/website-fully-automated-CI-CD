provider "aws" {
  region = var.aws_region
}

# Importar o módulo VPC, que já foi criado
module "vpc" {
  source = "./terraform/dev/vpc.tf" # Certifique-se de que o caminho esteja correto
}

# Importar o Security Group, se já tiver sido definido
module "security_group" {
  source = "./terraform/dev/security_groups.tf" # Certifique-se de que o caminho esteja correto
}

# Cluster ECS (já foi definido no `ecs.tf`)
module "ecs" {
  source = "./terraform/dev/ecs.tf"
}

# Load Balancer (importado do módulo ou definido separadamente)
module "load_balancer" {
  source = "./terraform/dev/load_balancer.tf"
}

# Outros módulos que já foram definidos para manter a estrutura modular
