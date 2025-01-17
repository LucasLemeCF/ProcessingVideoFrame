# variables.tf

# Região da AWS
variable "aws_region" {
  description = "Região onde os recursos serão provisionados"
  type        = string
  default     = "us-east-1"
}

# ID do Cognito User Pool
variable "COGNITO_USER_POOL_ID" {
  description = "ID do Cognito User Pool"
  type        = string
}

# ID do Cognito App Client
variable "COGNITO_CLIENT_ID" {
  description = "ID do Cognito App Client"
  type        = string
}

# ARN do Cognito User Pool
variable "COGNITO_USER_POOL_ARN" {
  description = "ARN do Cognito User Pool"
  type        = string
}
