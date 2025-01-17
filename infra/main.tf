provider "aws" {
  region = var.aws_region
}

# Função Lambda para processamento de frames
resource "aws_lambda_function" "register_user" {
  function_name = "frame_process_function" # Nome fixo da função Lambda

  handler = "process.lambda_handler" # Atualizado para o handler da função de registro
  runtime = "python3.8"
  role    = aws_iam_role.lambda_process_role.arn

  # Caminho para o código da função Lambda
  filename         = "../lambda/process/process_lambda_function.zip"
  source_code_hash = filebase64sha256("../lambda/process/process_lambda_function.zip")
}

# Role para Lambda
resource "aws_iam_role" "lambda_process_role" {
  name = "lambda_execution_role" # Nome fixo da role

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# Política de Permissões de envio de email para Lambda
resource "aws_iam_policy" "lambda_email_policy" {
  name        = "lambda_email_policy"
  description = "Permissões necessárias para a Lambda enviar emails"

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        "Resource" : "arn:aws:ses:us-east-1:440744219680:identity/*"
      }
    ]
  })
}

# Anexar a política à role da Lambda
resource "aws_iam_policy_attachment" "lambda_process_attachment" {
  name       = "lambda-policy-attachment"
  roles      = [aws_iam_role.lambda_process_role.name]
  policy_arn = aws_iam_policy.lambda_email_policy.arn
}
