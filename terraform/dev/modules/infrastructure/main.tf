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


resource "aws_ecs_cluster" "dev_cluster" {
  name = "dev-cluster"
}

resource "aws_ecs_task_definition" "frontend_task" {
  family                   = "dev-frontend-task"
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
        value = "http://${aws_lb.backend_lb.dns_name}"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/frontend"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "frontend"
      }
    }

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
          hostPort      = 8000
          protocol      = "tcp"
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
          value = "db-service.db.local"
        },
        {
          name  = "DB_PORT"
          value = "5432"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/backend"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/health/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 120
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
  task_definition = aws_ecs_task_definition.frontend_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.dev_subnet[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.frontend_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
    container_name   = "frontend"
    container_port   = 80
  }

  # Adiciona a dependência no ALB
  depends_on = [aws_lb.frontend_lb, aws_lb_target_group.frontend_target_group]

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
    security_groups  = [aws_security_group.backend_sg.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend_target_group.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb.backend_lb, aws_lb_target_group.backend_target_group]

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
    security_groups  = [aws_security_group.db_sg.id]
  }
  service_registries {
    registry_arn = aws_service_discovery_service.db_service_discovery.arn
  }
}

resource "aws_service_discovery_private_dns_namespace" "db_namespace" {
  name = "db.local"
  vpc  = aws_vpc.dev_vpc.id
}

resource "aws_service_discovery_service" "db_service_discovery" {
  name = "db-service"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.db_namespace.id
    dns_records {
      type = "A"
      ttl  = 60
    }
  }
  health_check_custom_config {
    failure_threshold = 1
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
  name        = "ecr_access_policy_dev"
  description = "Policy to access ECR repositories"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken"
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

resource "aws_iam_policy" "cloudwatch_logs_access" {
  name        = "cloudwatch_logs_access_policy"
  description = "Policy to allow ECS tasks to send logs to CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:log-group:/ecs/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_cloudwatch_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.cloudwatch_logs_access.arn
}


resource "aws_lb" "backend_lb" {
  name                       = "backend-lb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.backend_lb_sg.id]
  subnets                    = aws_subnet.dev_subnet[*].id
  enable_deletion_protection = false

  enable_cross_zone_load_balancing = true
  #   enable_http2                     = true

  tags = {

    Name = "backend-lb"

  }

  depends_on = [
    aws_internet_gateway.dev_igw,
    aws_subnet.dev_subnet
  ]
}

resource "aws_lb" "frontend_lb" {
  name                             = "frontend-lb"
  internal                         = false
  load_balancer_type               = "application"
  security_groups                  = [aws_security_group.frontend_lb_sg.id]
  subnets                          = aws_subnet.dev_subnet[*].id
  enable_deletion_protection       = false
  enable_cross_zone_load_balancing = true
  #   enable_http2                     = true

  tags = {
    Name = "frontend-lb"
  }

  depends_on = [
    aws_internet_gateway.dev_igw,
    aws_subnet.dev_subnet
  ]
}

# # Listener HTTPS para o Frontend
# resource "aws_lb_listener" "frontend_https_listener" {
#   load_balancer_arn = aws_lb.frontend_lb.arn
#   port              = 443
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
#   certificate_arn   = module.hosted_zone_acm.frontend_cert_ext.arn

#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.frontend_target_group.arn
#   }


# }

# Listener HTTPS para o Frontend
resource "aws_lb_listener" "frontend_http_listener" {
  load_balancer_arn = aws_lb.frontend_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_target_group.arn
  }


}


# # Listener HTTPS para o Backend
# resource "aws_lb_listener" "backend_https_listener" {
#   load_balancer_arn = aws_lb.backend_lb.arn
#   port              = 443
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
#   certificate_arn   = module.hosted_zone_acm.backend_cert_ext.arn

#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.backend_target_group.arn

#   }

# }


# Listener HTTPS para o Backend
resource "aws_lb_listener" "backend_http_listener" {
  load_balancer_arn = aws_lb.backend_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_target_group.arn

  }

}


resource "aws_lb_target_group" "backend_target_group" {
  name        = "backend-target-group-dev"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.dev_vpc.id
  target_type = "ip"

  health_check {
    path                = "/api/health/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "frontend_target_group" {
  name        = "frontend-target-group-dev"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.dev_vpc.id
  target_type = "ip" # Alterar para 'ip'


  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 5
    unhealthy_threshold = 2
  }
}

resource "aws_security_group" "db_sg" {
  vpc_id = aws_vpc.dev_vpc.id

  ingress {
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.backend_sg.id] # Permitir apenas o backend
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Permitir acesso à internet
  }

  tags = {
    Name = "db-sg"
  }
}


resource "aws_security_group" "backend_sg" {
  name        = "backend-sg"
  description = "Security group for Backend"
  vpc_id      = aws_vpc.dev_vpc.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.backend_lb_sg.id] # Permitir apenas o frontend
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = ["0.0.0.0/0"] # Permitir acesso à internet
  }

  tags = {
    Name = "backend-sg"
  }
}

resource "aws_security_group" "frontend_sg" {
  name        = "frontend-sg"
  description = "Security group for Frontend"
  vpc_id      = aws_vpc.dev_vpc.id

  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    # cidr_blocks     = ["0.0.0.0/0"] # Permitir acesso público
    security_groups = [aws_security_group.frontend_lb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "frontend-sg"
  }
}

resource "aws_security_group" "frontend_lb_sg" {
  name        = "frontend-lb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.dev_vpc.id


  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Permitir acesso público na porta 443 (HTTPS)
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Permitir acesso público na porta 80 (HTTP)
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "alb-sg"
  }
}

resource "aws_security_group" "backend_lb_sg" {
  name        = "backend-lb-sg"
  description = "Security group for Backend Load Balancer"
  vpc_id      = aws_vpc.dev_vpc.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.frontend_sg.id] # Permitir apenas o frontend
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Permitir acesso público na porta 80 (HTTP)
  }


  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "backend-lb-sg"
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

resource "aws_internet_gateway" "dev_igw" {
  vpc_id = aws_vpc.dev_vpc.id

  tags = {
    Name = "dev-igw"
  }
}

resource "aws_route_table" "dev_route_table" {
  vpc_id = aws_vpc.dev_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.dev_igw.id
  }

  tags = {
    Name = "dev-route-table"
  }
}

resource "aws_route_table_association" "dev_subnet_association" {
  count          = 2
  subnet_id      = aws_subnet.dev_subnet[count.index].id
  route_table_id = aws_route_table.dev_route_table.id
}

resource "aws_cloudwatch_log_group" "frontend_log_group" {
  name              = "/ecs/frontend"
  retention_in_days = 7 # Defina o tempo de retenção dos logs
}

resource "aws_cloudwatch_log_group" "backend_log_group" {
  name              = "/ecs/backend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "db_log_group" {
  name              = "/ecs/db"
  retention_in_days = 7
}





