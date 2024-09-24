VPC: dev_vpc (10.0.0.0/16)
|
|-- Subnets: dev_subnet[0] (10.0.1.0/24), dev_subnet[1] (10.0.2.0/24)
|
|-- Internet Gateway: dev_igw
|
|-- Route Table: dev_route_table (associado às subnets)
|
|-- Service Discovery:
|   |
|   |-- Namespace: db.local
|   |-- Service: db-service
|
|-- ECR Repositories:
|   |
|   |-- frontend-repo
|   |-- backend-repo
|
|-- IAM Roles and Policies:
|   |
|   |-- ecs_task_role:
|       - Policies:
|           - ecr_access_policy_dev
|           - cloudwatch_logs_access_policy
|
|-- CloudWatch Log Groups:
|   |
|   |-- /ecs/frontend
|   |-- /ecs/backend
|   |-- /ecs/db
|
|-- ALB: dev_lb (alb_sg)
|   |
|   |-- Listener: frontend_listener (porta 80, HTTP) -> Target Group: backend_target_group (porta 8000)
|
|-- Security Groups:
|   |
|   |-- alb_sg:
|       - Ingress: porta 80 de 0.0.0.0/0
|       - Egress: porta 8000 para backend_sg
|
|   |-- backend_sg:
|       - Ingress: porta 8000 do alb_sg
|       - Egress: all
|
|   |-- frontend_sg:
|       - Ingress: porta 80 de 0.0.0.0/0
|       - Egress: all
|
|   |-- db_sg:
|       - Ingress: porta 5432 de backend_sg
|       - Egress: porta 5432 para backend_sg
|
|-- ECS Cluster: dev_cluster
|   |
|   |-- ECS Services:
|       |
|       |-- frontend_service:
|           - Task Definition: frontend_task
|           - Security Group: frontend_sg
|
|       |-- backend_service:
|           - Task Definition: backend_task
|           - Security Group: backend_sg
|
|       |-- db_service:
|           - Task Definition: db_task
|           - Security Group: db_sg
|           - Service Discovery: db-service.db.local
