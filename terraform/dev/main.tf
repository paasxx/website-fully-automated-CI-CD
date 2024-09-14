provider "aws" {
  region = var.aws_region
}

# Importar o módulo VPC, que já foi criado
module "vpc" {
  source = "./vpc" # Certifique-se de que o caminho esteja correto
}

# Importar o Security Group, se já tiver sido definido
module "security_group" {
  source = "./security_group" # Certifique-se de que o caminho esteja correto
}

# Cluster ECS (já foi definido no `ecs.tf`)
module "ecs" {
  source = "./ecs"
}

# Load Balancer (importado do módulo ou definido separadamente)
module "load_balancer" {
  source = "./load_balancer"
}

# Outros módulos que já foram definidos para manter a estrutura modular
