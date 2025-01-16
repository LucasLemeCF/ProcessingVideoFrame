provider "aws" {
  region = var.aws_region
}

# Função Lambda para Registro de Usuário
resource "aws_lambda_function" "register_user" {
  function_name = "user_register_function" # Nome fixo da função Lambda

  handler = "register.lambda_handler" # Atualizado para o handler da função de registro
  runtime = "python3.8"
  role    = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      COGNITO_USER_POOL_ID = var.COGNITO_USER_POOL_ID
      COGNITO_CLIENT_ID    = var.COGNITO_CLIENT_ID
    }
  }

  # Caminho para o código da função Lambda
  filename         = "../lambda/register/register_lambda_function.zip"
  source_code_hash = filebase64sha256("../lambda/register/register_lambda_function.zip")
}

# Função Lambda para Login de Usuário
resource "aws_lambda_function" "login_user" {
  function_name = "user_login_function" # Nome fixo da função Lambda

  handler = "login.lambda_handler" # Atualizado para o handler da função de login
  runtime = "python3.8"
  role    = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      COGNITO_USER_POOL_ID = var.COGNITO_USER_POOL_ID
      COGNITO_CLIENT_ID    = var.COGNITO_CLIENT_ID
    }
  }

  # Caminho para o código da função Lambda
  filename         = "../lambda/login/login_lambda_function.zip"
  source_code_hash = filebase64sha256("../lambda/login/login_lambda_function.zip")
}

# Role para Lambda
resource "aws_iam_role" "lambda_role" {
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

# Política de Permissões do Cognito para Lambda
resource "aws_iam_policy" "lambda_cognito_policy" {
  name        = "lambda_cognito_policy"
  description = "Permissões necessárias para a Lambda registrar usuários no Cognito e autenticar login"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cognito-idp:SignUp",          # Permissão para registrar usuários no Cognito
          "cognito-idp:InitiateAuth",    # Permissão para iniciar autenticação (login) no Cognito
          "cognito-idp:AdminCreateUser", # Permissão adicional para criar usuários se necessário
          "cognito-idp:RespondToAuthChallenge",
          "lambda:GetFunction" # Permissão para a Lambda acessar o código de outra função Lambda (caso precise)
        ]
        Effect   = "Allow"
        Resource = var.COGNITO_USER_POOL_ARN # A política será aplicada para o ARN do Pool de Usuários
      },
      {
        Action = [
          "cognito-idp:AdminConfirmSignUp",   # Permissão para confirmar o cadastro de um novo usuário
          "cognito-idp:AdminSetUserPassword", # Permissão para configurar ou redefinir senhas dos usuários
          "cognito-idp:AdminGetUser"          # Adicionada permissão para obter informações do usuário (necessária para a Lambda)
        ]
        Effect   = "Allow"
        Resource = var.COGNITO_USER_POOL_ARN
      }
    ]
  })
}

# Anexar a política à role da Lambda
resource "aws_iam_policy_attachment" "lambda_policy_attachment" {
  name       = "lambda-policy-attachment"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = aws_iam_policy.lambda_cognito_policy.arn
}
