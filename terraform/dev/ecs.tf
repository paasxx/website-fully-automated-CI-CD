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
        value = "http://${aws_lb.app_lb.dns_name}/api/"
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
      image     = "${aws_ecr_repository.backend_repo.repository_url}:latest"
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
  task_definition = aws_ecs_task_definition.frontend_task.arn
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
    target_group_arn = aws_lb_target_group.backend_target_group.arn
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
