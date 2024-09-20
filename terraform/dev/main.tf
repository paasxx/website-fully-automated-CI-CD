# Data source para obter zonas de disponibilidade
data "aws_availability_zones" "available" {}

provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "frontend" {
  name = "frontend-repo"
}

resource "aws_ecr_repository" "backend" {
  name = "backend-repo"
}

# Adiciona o repositório ECR à política de acesso do ECS
resource "aws_iam_role_policy_attachment" "ecs_ecr" {
  policy_arn = aws_iam_policy.ecr_access.arn
  role       = aws_iam_role.ecs_task_role.name
}


resource "aws_ecs_cluster" "dev_cluster" {
  name = "dev-cluster"
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "frontend-task"
  execution_role_arn       = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{
    name  = "frontend"
    image = "${aws_ecr_repository.frontend.repository_url}:latest"
    portMappings = [{
      containerPort = 80
      hostPort      = 80
      protocol      = "tcp"
    }]
    environment = [
      {
        name  = "REACT_APP_BACKEND_URL"
        value = "http://${aws_lb.dev_lb.dns_name}/api/"
      }
    ]
  }])
}

resource "aws_ecs_task_definition" "backend_task" {
  family                   = "dev-backend-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:latest"
      essential = true
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
          value = var.db_password
        },
        {
          name  = "DB_HOST"
          value = "127.0.0.1"
        },
        {
          name  = "DB_PORT"
          value = "5432"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/kanastra-dev"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "db_task" {
  family                   = "db-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "db"
      image     = var.db_image # Exemplo: "postgres:13" ou "mysql:8"
      essential = true
      environment = [
        {
          name  = "POSTGRES_USER"
          value = var.db_user
        },
        {
          name  = "POSTGRES_PASSWORD"
          value = var.db_password
        },
        {
          name  = "POSTGRES_DB"
          value = var.db_name
        }
      ]
      portMappings = [
        {
          containerPort = var.db_port # Exemplo: 5432 para PostgreSQL, 3306 para MySQL
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/db"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "db"
        }
      }
    }
  ])
}




resource "aws_ecs_service" "frontend_service" {
  name            = "frontend-service"
  cluster         = aws_ecs_cluster.dev_cluster.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.dev_subnet[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.dev_sg.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend_target_group.arn
    container_name   = "frontend"
    container_port   = 80
  }
}

resource "aws_ecs_service" "backend_service" {
  name            = "backend-service"
  cluster         = aws_ecs_cluster.dev_cluster.id
  task_definition = aws_ecs_task_definition.backend_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.dev_subnet[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.dev_sg.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
}

resource "aws_ecs_service" "db_service" {
  name            = "db-service"
  cluster         = aws_ecs_cluster.dev_cluster.id
  task_definition = aws_ecs_task_definition.db_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.dev_subnet[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.dev_sg.id]
  }
}



resource "aws_iam_role" "ecs_task_role" {
  name = "ecs_task_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "ecr_access" {
  name        = "ecr_access_policy"
  description = "Policy to access ECR repositories"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecr_access.arn
}


resource "aws_lb" "dev_lb" {
  name                       = "dev-lb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.dev_sg.id]
  subnets                    = aws_subnet.dev_subnet[*].id
  enable_deletion_protection = false

  enable_cross_zone_load_balancing = true
  enable_http2                     = true

  tags = {
    Name = "dev-lb"
  }
}


resource "aws_lb_target_group" "frontend_target_group" {
  name     = "frontend-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.dev_vpc.id

}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.dev_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
  }
}

resource "aws_lb_target_group" "backend_target_group" {
  name     = "backend-target-group"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.dev_vpc.id
}


resource "aws_security_group" "dev_sg" {
  vpc_id = aws_vpc.dev_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "dev-sg"
  }
}


resource "aws_vpc" "dev_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "dev-vpc"
  }
}

resource "aws_subnet" "dev_subnet" {
  count = 2

  vpc_id                  = aws_vpc.dev_vpc.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = element(data.aws_availability_zones.available.names, count.index)
  map_public_ip_on_launch = true
  tags = {
    Name = "dev-subnet-${count.index}"
  }
}

resource "aws_s3_bucket" "meu_bucket_terraform" {
  bucket = "meu-bucket-terraform"
  acl    = "private"
  tags = {
    Name        = "meu-bucket-terraform"
    Environment = "dev"
  }
}


terraform {
  backend "s3" {
    bucket = "meu-bucket-terraform"
    key    = "terraform/dev/terraform.tfstate"
    region = "us-east-1"
  }
}

