resource "aws_ecs_task_definition" "frontend_task_prod" {
  family                   = "frontend-task-prod"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = "arn:aws:iam::${var.aws_account_id}:role/ecsTaskExecutionRole"

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${var.ecr_registry}/frontend:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/kanastra-prod"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "backend_task_prod" {
  family                   = "backend-task-prod"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = "arn:aws:iam::${var.aws_account_id}:role/ecsTaskExecutionRole"

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${var.ecr_registry}/backend:latest"
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
          value = var.db_password  # Usando a variável
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
          awslogs-group         = "/ecs/kanastra-prod"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "db_task_prod" {
  family                   = "db-task-prod"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = "arn:aws:iam::${var.aws_account_id}:role/ecsTaskExecutionRole"

  container_definitions = jsonencode([
    {
      name      = "db"
      image     = "postgres"
      essential = true
      memory    = 512
      cpu       = 256
      portMappings = [
        {
          containerPort = 5432
        }
      ]
      environment = [
        {
          name  = "POSTGRES_DB"
          value = "kanastra_db"
        },
        {
          name  = "POSTGRES_USER"
          value = "kanastra_user"
        },
        {
          name  = "POSTGRES_PASSWORD"
          value = var.db_password  # Usando a variável
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/kanastra-prod"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "db"
        }
      }
    }
  ])
}
