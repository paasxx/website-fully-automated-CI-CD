# main.tf

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
  tags = {
    Name = "main-vpc"
  }
}

# Subnets
resource "aws_subnet" "subnet1" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
  tags = {
    Name = "subnet1"
  }
}

# Security Group
resource "aws_security_group" "ecs_sg" {
  vpc_id = aws_vpc.main.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "ecs_sg"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "kanastra" {
  name = "kanastra-cluster"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "kanastra" {
  family                   = "kanastra-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${var.ecr_repo_backend}:latest"
    memory    = 512
    cpu       = 256
    portMappings = [
      {
        containerPort = 8000
      }
    ]
    environment = [
      {
        name  = "DB_NAME"
        value = "kanastra_db"
      },
      {
        name  = "DB_USER"
        value = "kanastra_user"
      },
      {
        name  = "DB_PASSWORD"
        value = "mypassword"
      },
      {
        name  = "DB_HOST"
        value = "db"
      },
      {
        name  = "DB_PORT"
        value = "5432"
      }
    ]
  }, {
    name      = "frontend"
    image     = "${var.ecr_repo_frontend}:latest"
    memory    = 512
    cpu       = 256
    portMappings = [
      {
        containerPort = 80
      }
    ]
  }])
}

# ECS Service for Backend
resource "aws_ecs_service" "backend" {
  name            = "backend-service"
  cluster         = aws_ecs_cluster.kanastra.id
  task_definition = aws_ecs_task_definition.kanastra.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = [aws_subnet.subnet1.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend_target_group.arn
    container_name   = "backend"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.frontend_listener]
}

# ECS Service for Frontend
resource "aws_ecs_service" "frontend" {
  name            = "frontend-service"
  cluster         = aws_ecs_cluster.kanastra.id
  task_definition = aws_ecs_task_definition.kanastra.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = [aws_subnet.subnet1.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
    container_name   = "frontend"
    container_port   = 80
  }
  depends_on = [aws_lb_listener.frontend_listener]
}

# Load Balancer
resource "aws_lb" "main" {
  name               = "main-load-balancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ecs_sg.id]
  subnets            = [aws_subnet.subnet1.id]

  enable_deletion_protection = false
  enable_cross_zone_load_balancing = true
  idle_timeout = 60
}

# Load Balancer Target Groups
resource "aws_lb_target_group" "backend_target_group" {
  name     = "backend-target-group"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}

resource "aws_lb_target_group" "frontend_target_group" {
  name     = "frontend-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}

# Load Balancer Listeners
resource "aws_lb_listener" "frontend_listener" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "404: Page Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener" "backend_listener" {
  load_balancer_arn = aws_lb.main.arn
  port              = 8000
  protocol          = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.backend_target_group.arn
  }
}
