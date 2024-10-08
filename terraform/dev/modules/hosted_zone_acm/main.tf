
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


# # Validação do Certificado SSL do Frontend via DNS
# resource "aws_route53_record" "frontend_cert_ext_validation" {
#   for_each = { for dvo in aws_acm_certificate.frontend_cert_ext.domain_validation_options : dvo.domain_name => dvo }

#   zone_id = aws_route53_zone.my_zone.zone_id
#   name    = each.value.resource_record_name
#   type    = each.value.resource_record_type
#   ttl     = 60
#   records = [each.value.resource_record_value]

#   depends_on = [aws_acm_certificate.frontend_cert_ext]
# }

# # Validação do Certificado SSL do Backend via DNS
# resource "aws_route53_record" "backend_cert_ext_validation" {
#   for_each = { for dvo in aws_acm_certificate.backend_cert_ext.domain_validation_options : dvo.domain_name => dvo }

#   zone_id = aws_route53_zone.my_zone.zone_id
#   name    = each.value.resource_record_name
#   type    = each.value.resource_record_type
#   ttl     = 60
#   records = [each.value.resource_record_value]

#   depends_on = [aws_acm_certificate.backend_cert_ext]
# }


# Registro DNS para o domínio frontend (www.teudominio.com)
resource "aws_route53_record" "frontend_www" {
  zone_id = aws_route53_zone.my_zone.zone_id
  name    = "www.candlefarm.com.br"
  type    = "A"

  alias {
    name                   = aws_lb.frontend_lb.dns_name
    zone_id                = aws_lb.frontend_lb.zone_id
    evaluate_target_health = true
  }
}

# Registro DNS para o domínio backend (api.teudominio.com)
resource "aws_route53_record" "backend_api" {
  zone_id = aws_route53_zone.my_zone.zone_id
  name    = "api.candlefarm.com.br"
  type    = "A"

  alias {
    name                   = aws_lb.backend_lb.dns_name
    zone_id                = aws_lb.backend_lb.zone_id
    evaluate_target_health = true
  }
}

