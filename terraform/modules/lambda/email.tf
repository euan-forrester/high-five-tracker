resource "aws_ses_email_identity" "from_email" {
  email = var.from_email
}
