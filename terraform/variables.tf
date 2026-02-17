variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "extraction-job-api"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "extraction_jobs"
}

variable "auth0_domain" {
  description = "Auth0 domain for JWT validation"
  type        = string
  default     = "dev-wkl17exhgoi6mj0m.us.auth0.com"
}

variable "auth0_audience" {
  description = "Auth0 API audience"
  type        = string
  default     = "https://dev-wkl17exhgoi6mj0m.us.auth0.com/api/v2/"
}

variable "auth_disabled" {
  description = "Set to 1 to disable auth (for testing)"
  type        = string
  default     = "0"
}
