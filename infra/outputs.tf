output "lambda_register_function_name" {
  value = aws_lambda_function.register_user.function_name
}

output "lambda_register_function_arn" {
  value = aws_lambda_function.register_user.arn
}
