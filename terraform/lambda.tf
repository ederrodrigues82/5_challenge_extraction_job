# IAM role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy (VPC, CloudWatch logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "main" {
  filename         = "${path.module}/../lambda.zip"
  function_name    = var.project_name
  role             = aws_iam_role.lambda.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.11"
  source_code_hash = filebase64sha256("${path.module}/../lambda.zip")

  memory_size = 512
  timeout     = 30

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL  = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${var.db_name}"
      AUTH0_DOMAIN  = var.auth0_domain
      AUTH0_AUDIENCE = var.auth0_audience
      AUTH_DISABLED = var.auth_disabled
    }
  }

  depends_on = [aws_db_instance.main]
}

# Allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
