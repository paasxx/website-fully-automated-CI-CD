output "frontend_repo_url" {
  value = aws_ecr_repository.frontend_repo.repository_url
}

output "backend_repo_url" {
  value = aws_ecr_repository.backend_repo.repository_url
}

output "load_balancer_dns" {
  value = aws_lb.dev_lb.dns_name
}
