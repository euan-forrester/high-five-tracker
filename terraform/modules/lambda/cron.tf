resource "aws_cloudwatch_event_rule" "cron" {
  name        = "${var.application_name}-cron-rule-${var.environment}"
  is_enabled = true
  description = "Fire our lambda expression"
  schedule_expression = "cron(0 16 * * ? *)"  # Run every day at 4:00 PM UTC = 9:00 AM PDT or 8:00 AM PST
}

resource "aws_cloudwatch_event_target" "cron" {
  rule      = aws_cloudwatch_event_rule.cron.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.high_fives.arn
}
