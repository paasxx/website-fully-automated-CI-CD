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

output "frontend_lb_zone_id" {
  value = aws_lb.frontend_lb.zone_id
}

output "backend_lb_zone_id" {
  value = aws_lb.backend_lb.zone_id
}

output "frontend_lb_arn" {
  value = aws_lb.frontend_lb.arn
}

output "backend_lb_arn" {
  value = aws_lb.backend_lb.arn
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend_target_group.arn
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend_target_group.arn
}

