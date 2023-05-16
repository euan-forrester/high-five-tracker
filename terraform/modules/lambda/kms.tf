# Just have one KMS key that everyone references to save on billing costs

resource "aws_kms_key" "parameter_secrets" {
  description             = "Used to encrypt/decrypt secrets in the Parameter Store ${var.environment}"
  key_usage               = "ENCRYPT_DECRYPT"
  enable_key_rotation     = true
  deletion_window_in_days = 7
}
