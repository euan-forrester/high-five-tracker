resource "aws_cloudwatch_event_rule" "cron" {
  name        = "${var.application_name}-cron-rule-${var.environment}"
  is_enabled = true
  description = "Fire our lambda expression"
  # Note that these need to be Quartz cron expressions, not unix cron
  schedule_expression = "cron(0 16 * * ? *)"  # Run every day at 4:00 PM UTC = 9:00 AM PDT or 8:00 AM PST
  #schedule_expression = "cron(*/5 * * * ? *)"  # Run every 5 minutes for testing
}

resource "aws_cloudwatch_event_target" "cron" {
  rule      = aws_cloudwatch_event_rule.cron.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.high_fives.arn
}
