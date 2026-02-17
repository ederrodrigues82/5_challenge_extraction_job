# DB subnet group - use default subnets
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = data.aws_subnets.default.ids
}

# RDS PostgreSQL instance
resource "aws_db_instance" "main" {
  identifier     = var.project_name
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  allocated_storage     = 20
  storage_type          = "gp3"
  max_allocated_storage = 0

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false

  skip_final_snapshot = true
}
