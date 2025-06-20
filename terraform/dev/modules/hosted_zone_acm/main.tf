
provider "aws" {
  region = var.aws_region
}

resource "aws_acm_certificate" "frontend_cert_ext" {
  domain_name       = "www.candlefarm.com.br" # Substitua pelo seu domínio
  validation_method = "DNS"

  subject_alternative_names = ["candlefarm.com.br"]

  tags = {
    Name = "frontend-cert"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate" "backend_cert_ext" {
  domain_name       = "api.candlefarm.com.br" # Substitua pelo seu subdomínio do backend
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "backend-cert"
  }
}


# Hosted Zone no Route 53
resource "aws_route53_zone" "my_zone" {
  name = "candlefarm.com.br" # Substitua pelo seu domínio
}


# Validação do Certificado SSL do Frontend via DNS
resource "aws_route53_record" "frontend_cert_ext_validation" {
  for_each = { for dvo in aws_acm_certificate.frontend_cert_ext.domain_validation_options : dvo.domain_name => dvo }

  zone_id = aws_route53_zone.my_zone.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  ttl     = 60
  records = [each.value.resource_record_value]

  depends_on = [aws_acm_certificate.frontend_cert_ext]
}

# Validação do Certificado SSL do Backend via DNS
resource "aws_route53_record" "backend_cert_ext_validation" {
  for_each = { for dvo in aws_acm_certificate.backend_cert_ext.domain_validation_options : dvo.domain_name => dvo }

  zone_id = aws_route53_zone.my_zone.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  ttl     = 60
  records = [each.value.resource_record_value]

  depends_on = [aws_acm_certificate.backend_cert_ext]
}


# Registro DNS para o domínio frontend (www.teudominio.com)
resource "aws_route53_record" "frontend_www" {
  zone_id = aws_route53_zone.my_zone.zone_id
  name    = "www.candlefarm.com.br"
  type    = "A"

  alias {
    name                   = var.frontend_lb_dns
    zone_id                = var.frontend_lb_id
    evaluate_target_health = true
  }
}

# Registro DNS para o domínio backend (api.teudominio.com)
resource "aws_route53_record" "backend_api" {
  zone_id = aws_route53_zone.my_zone.zone_id
  name    = "api.candlefarm.com.br"
  type    = "A"

  alias {
    name                   = var.backend_lb_dns
    zone_id                = var.backend_lb_id
    evaluate_target_health = true
  }
}

# Listener HTTPS para o Frontend
resource "aws_lb_listener" "frontend_https_listener" {
  load_balancer_arn = var.frontend_lb_arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.frontend_cert_ext.arn

  default_action {
    type             = "forward"
    target_group_arn = var.frontend_target_group_arn
  }


}

# Listener HTTPS para o Backend
resource "aws_lb_listener" "backend_https_listener" {
  load_balancer_arn = var.backend_lb_arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.backend_cert_ext.arn

  default_action {
    type             = "forward"
    target_group_arn = var.backend_target_group_arn
  }

}
