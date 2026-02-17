# Use default VPC for simplicity (Lambda has internet access for Auth0 JWKS)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for Lambda - allow outbound to RDS and internet (Auth0)
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project_name}-lambda-"
  description = "Lambda outbound to RDS and internet"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security group for RDS - allow inbound 5432 from Lambda only
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "Allow Lambda to connect to RDS PostgreSQL"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "PostgreSQL from Lambda"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}
