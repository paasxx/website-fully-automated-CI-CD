variable "aws_region" {
  description = "The AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}


variable "frontend_lb_dns" {
  type = string
}

variable "backend_lb_dns" {
  type = string
}

variable "frontend_lb_id" {
  type = string
}

variable "backend_lb_id" {
  type = string
}

variable "frontend_lb_arn" {
  type = string
}

variable "backend_lb_arn" {
  type = string
}

variable "frontend_target_group_arn" {
  type = string
}

variable "backend_target_group_arn" {
  type = string
}





