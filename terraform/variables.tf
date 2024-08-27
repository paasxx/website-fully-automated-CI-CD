# variables.tf

variable "aws_region" {
  description = "The AWS region where resources will be created."
  type        = string
  default     = "us-east-1"
}

variable "ecr_repo_backend" {
  description = "The ECR repository URI for the backend."
  type        = string
}

variable "ecr_repo_frontend" {
  description = "The ECR repository URI for the frontend."
  type        = string
}
