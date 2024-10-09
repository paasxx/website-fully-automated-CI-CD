# Data source para obter zonas de disponibilidade
data "aws_availability_zones" "available" {}

provider "aws" {
  region = var.aws_region
}


# Módulo para Hosted Zone e ACM
module "hosted_zone_acm" {
  source = "./modules/hosted_zone_acm"

}

# Módulo para Infraestrutura (ECS, ALB, etc.)
module "infrastructure" {
  source         = "./modules/infrastructure"
  aws_account_id = var.aws_account_id
  db_password    = var.db_password
}


