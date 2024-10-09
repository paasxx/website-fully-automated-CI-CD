variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}


# Saídas (outputs) dos LBs que serão usados na Fase 2
variable "frontend_lb_dns" {
  type = string
}

variable "backend_lb_dns" {
  type = string
}

# Saídas (outputs) dos LBs que serão usados na Fase 2
variable "frontend_lb_id" {
  type = string
}

variable "backend_lb_id" {
  type = string
}



