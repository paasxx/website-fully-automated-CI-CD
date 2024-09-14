output "load_balancer_dns" {
  description = "DNS do Load Balancer"
  value       = aws_lb.frontend_lb.dns_name
}

output "ecs_cluster_name" {
  description = "Nome do cluster ECS"
  value       = aws_ecs_cluster.cluster.name
}
