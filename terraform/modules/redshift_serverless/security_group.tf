resource "aws_security_group" "serverless" {
  name        = "${var.namespace_name}-redshift-serverless"
  description = "Security group for Redshift serverless cluster ${var.namespace_name}"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_security_group_rule" "redhsift_allow_port_from_vpc" {
  type              = "ingress"
  from_port         = 5439
  to_port           = 5439
  protocol          = "tcp"
  cidr_blocks       = var.allowed_cidr
  security_group_id = aws_security_group.serverless.id
}


resource "aws_security_group_rule" "redhsift_self" {
  count             = var.sg_enable_self ? 1 : 0
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  self              = true
  security_group_id = aws_security_group.serverless.id
}



