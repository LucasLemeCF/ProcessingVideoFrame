provider "aws" {
  region = var.aws_region
}

# Função Lambda para processamento de frames.
resource "aws_lambda_function" "register_user" {
  function_name = "frame_process_function" # Nome fixo da função Lambda

  handler = "process.lambda_handler" # Atualizado para o handler da função de procesamento
  runtime = "python3.11"
  role    = aws_iam_role.lambda_process_role.arn
  timeout = 900 # Definir o tempo de execução para 15 minutos

  # Caminho para o código da função Lambda.
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

# Política de Permissões de acesso ao S3
resource "aws_iam_policy" "lambda_email_policy" {
  name        = "lambda_email_policy"
  description = "Permissões necessárias para a Lambda acessar o S3"

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

# Política de Permissão para SQS
resource "aws_iam_policy" "lambda_sqs_send_policy" {
  name        = "lambda_sqs_policy"
  description = "Permissões para a Lambda acessar a fila SQS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "sqs:ReceiveMessage",
          "sqs:GetQueueAttributes",
          "sqs:sendmessage",
          "sqs:DeleteMessage"
        ],
        "Resource" : "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.sqs_queue_name}"
      }
    ]
  })
}

# Anexar a política do S3 à role da Lambda
resource "aws_iam_policy_attachment" "lambda_process_attachment" {
  name       = "lambda-policy-attachment"
  roles      = [aws_iam_role.lambda_process_role.name]
  policy_arn = aws_iam_policy.lambda_email_policy.arn
}

# Anexar a política de SQS à role da Lambda
resource "aws_iam_role_policy_attachment" "lambda_sqs_policy_process_attachment" {
  role       = aws_iam_role.lambda_sendemail_role.name
  policy_arn = aws_iam_policy.lambda_sqs_send_policy.arn
}
