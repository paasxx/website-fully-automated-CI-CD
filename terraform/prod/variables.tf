variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"  # Valor padrão
}

variable "aws_account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "ecr_registry" {
  description = "The ECR registry URL"
  type        = string
}

variable "db_password" {
  description = "The database password"
  type        = string
}
