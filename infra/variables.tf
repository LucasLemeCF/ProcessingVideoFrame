# Região da AWS
variable "aws_region" {
  description = "Região onde os recursos serão provisionados"
  type        = string
  default     = "us-east-1"
}

# Nome da fila SQS
variable "sqs_queue_name" {
  description = "Nome da fila SQS"
  type        = string
}
