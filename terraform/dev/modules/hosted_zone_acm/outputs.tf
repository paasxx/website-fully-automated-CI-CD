# Outputs para serem usados no módulo de infraestrutura
output "frontend_cert_arn" {
  value = aws_acm_certificate.frontend_cert_ext.arn
}

output "backend_cert_arn" {
  value = aws_acm_certificate.backend_cert_ext.arn
}

output "route53_ns_records" {
  description = "NS records for the Route 53 hosted zone"
  value       = aws_route53_zone.my_zone.name_servers
}

