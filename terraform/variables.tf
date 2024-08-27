variable "aws_region" {
  description = "The AWS region"
  type        = string
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC"
  type        = string
}

variable "subnet1_cidr_block" {
  description = "The CIDR block for the first subnet"
  type        = string
}

variable "subnet2_cidr_block" {
  description = "The CIDR block for the second subnet"
  type        = string
}

variable "ecr_repo_backend" {
  description = "The name of the ECR repository for the backend"
  type        = string
}

variable "ecr_repo_frontend" {
  description = "The name of the ECR repository for the frontend"
  type        = string
}

variable "aws_account_id" {
  description = "The AWS Account ID"
  type        = string
}

variable "aws_subnet" {
  description = "The subnet ID for the ECS service"
  type        = list(string)
}

variable "aws_security_group" {
  description = "The security group ID for the ECS service"
  type        = string
}

variable "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  type        = string
}

variable "target_group_arn" {
  description = "The ARN of the target group for the load balancer"
  type        = string
}
