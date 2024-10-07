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

output "route53_ns_records" {
  description = "NS records for the Route 53 hosted zone"
  value       = aws_route53_zone.my_zone.name_servers
}

output "acm_certificate_arn" {
  description = "The ARN of the ACM certificate"
  value       = aws_acm_certificate.frontend_cert.arn
}
