# Saídas (outputs) dos LBs que serão usados na Fase 2
output "frontend_lb_dns" {
  value = module.infrastructure.frontend_lb.dns_name
}

output "backend_lb_dns" {
  value = module.infrastructure.backend_lb.dns_name
}

# Saídas (outputs) dos LBs que serão usados na Fase 2
output "frontend_lb_id" {
  value = module.infrastructure.frontend_lb.zone_id
}

output "backend_lb_id" {
  value = module.infrastructure.backend_lb.zone_id
}


