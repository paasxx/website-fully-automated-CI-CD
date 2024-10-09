# Data source para obter zonas de disponibilidade
data "aws_availability_zones" "available" {}

provider "aws" {
  region = var.aws_region
}


# Módulo para Infraestrutura (ECS, ALB, etc.)
module "infrastructure" {
  source         = "./modules/infrastructure"
  aws_account_id = var.aws_account_id
  db_password    = var.db_password
}


module "hosted_zone_acm" {
  source = "./modules/hosted_zone_acm"

  # Passe os valores de saída dos LBs como variáveis
  frontend_lb_dns = module.infrastructure.frontend_lb.dns_name
  backend_lb_dns  = module.infrastructure.backend_lb.dns_name
  frontend_lb_id  = module.infrastructure.frontend_lb.zone_id
  backend_lb_id   = module.infrastructure.backend_lb.zone_id
}

