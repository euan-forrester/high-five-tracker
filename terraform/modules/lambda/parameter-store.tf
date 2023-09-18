resource "aws_ssm_parameter" "base_url" {
  name        = "/${var.application_name}/${var.environment}/base-url"
  description = "Base URL from which to get High Fives"
  type        = "String"
  value       = var.base_url
}

resource "aws_ssm_parameter" "batch_size" {
  name        = "/${var.application_name}/${var.environment}/batch-size"
  description = "How many High Fives to get in a single call"
  type        = "String"
  value       = var.batch_size
}

resource "aws_ssm_parameter" "request_retries" {
  name        = "/${var.application_name}/${var.environment}/num-retries"
  description = "How many times to retry our request"
  type        = "String"
  value       = var.num_retries
}

resource "aws_ssm_parameter" "request_backoff_factor" {
  name        = "/${var.application_name}/${var.environment}/retry-backoff-factor"
  description = "Number of seconds to add to backoff amount for each failed request"
  type        = "String"
  value       = var.retry_backoff_factor
}

resource "aws_ssm_parameter" "names_of_interest" {
  name        = "/${var.application_name}/${var.environment}/names-of-interest"
  description = "JSON-formatted array of the names we're looking for in High Fives"
  type        = "String"
  value       = var.names_of_interest
}

resource "aws_ssm_parameter" "communities_of_interest" {
  name        = "/${var.application_name}/${var.environment}/communities-of-interest"
  description = "JSON-formatted array of the communities in which we are looking for our names of interest in High Fives"
  type        = "String"
  value       = var.communities_of_interest
}

# Arguably we should make this encrypted, but it costs money to maintain the KMS key
resource "aws_ssm_parameter" "target_email" {
  name        = "/${var.application_name}/${var.environment}/target-email"
  description = "Email address to send our High Fives of interest to"
  type        = "String"
  value       = var.target_email
}

# Arguably we should make this encrypted, but it costs money to maintain the KMS key
resource "aws_ssm_parameter" "from_email" {
  name        = "/${var.application_name}/${var.environment}/from-email"
  description = "Email address from which our emails come"
  type        = "String"
  value       = var.from_email
}
