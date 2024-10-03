output "frontend_repo_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "backend_repo_url" {

  value = aws_ecr_repository.backend.repository_url
}

output "frontend_lb_dns" {
  value = aws_lb.frontend_lb.dns_name
}

output "backend_lb_dns" {
  value = aws_lb.backend_lb.dns_name
}
