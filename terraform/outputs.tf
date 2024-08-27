output "ecr_repository_url" {
  value = aws_ecr_repository.my_repository.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.my_cluster.name
}

output "load_balancer_dns" {
  value = aws_lb.my_load_balancer.dns_name
}

# outputs.tf

output "load_balancer_url" {
  description = "The URL of the Load Balancer."
  value       = aws_lb.main.dns_name
}
