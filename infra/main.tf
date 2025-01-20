provider "aws" {
  region = var.aws_region
}

# Recurso da camada Lambda.
resource "aws_lambda_layer_version" "ffmpeg_layer" {
  filename            = "../ffmpeg.zip"
  layer_name          = "ffmpeg_layer"
  compatible_runtimes = ["python3.8"]
}

# Função Lambda para processamento de frames
resource "aws_lambda_function" "register_user" {
  function_name = "frame_process_function" # Nome fixo da função Lambda

  handler = "process.lambda_handler" # Atualizado para o handler da função de procesamento
  runtime = "python3.8"
  role    = aws_iam_role.lambda_process_role.arn

  # Caminho para o código da função Lambda.
  filename         = "../lambda/process/process_lambda_function.zip"
  source_code_hash = filebase64sha256("../lambda/process/process_lambda_function.zip")

  # Configuração de camadas
  layers = [aws_lambda_layer_version.ffmpeg_layer.arn]
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
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:PutObject",
          "s3:PutObjectAcl"
        ],
        "Resource" : "arn:aws:s3:::*"
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
