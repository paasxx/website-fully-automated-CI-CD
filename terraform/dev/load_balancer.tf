resource "aws_lb" "dev_lb" {
  name                       = "dev-lb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.dev_sg.id]
  subnets                    = aws_subnet.dev_subnet[*].id
  enable_deletion_protection = false

  enable_cross_zone_load_balancing = true
  enable_http2                     = true

  tags = {
    Name = "dev-lb"
  }
}


resource "aws_lb_target_group" "frontend" {
  name     = "frontend-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = dev_vpc.id

}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.dev_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_target_group" "backend" {
  name     = "backend-target-group"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = dev_vpc.id
}
