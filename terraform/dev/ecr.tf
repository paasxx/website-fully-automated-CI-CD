
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
