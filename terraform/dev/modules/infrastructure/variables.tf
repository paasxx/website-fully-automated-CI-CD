variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "The AWS account ID"
  type        = string
}


variable "db_image" {
  description = "Imagem do container para o banco de dados"
  type        = string
  default     = "postgres" # Altere para MySQL, se necessário
}

variable "db_user" {
  description = "Nome de usuário do banco de dados"
  type        = string
  default     = "kanastra_user"
}

variable "db_password" {
  description = "Senha do banco de dados"
  type        = string
}

variable "db_name" {
  description = "Nome do banco de dados"
  type        = string
  default     = "kanastra_db"
}

variable "db_port" {
  description = "Porta do banco de dados"
  type        = number
  default     = 5432 # PostgreSQL
}
