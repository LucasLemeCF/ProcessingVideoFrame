# variables.tf

# Região da AWS
variable "aws_region" {
  description = "Região onde os recursos serão provisionados"
  type        = string
  default     = "us-east-1"
}
