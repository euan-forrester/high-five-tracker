resource "aws_cloudwatch_metric_alarm" "eventbridge_failedinvocations" {
  alarm_name                = "${var.application_name} EventBridge FailedInvocations - ${var.environment}"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "1"
  metric_name               = "FailedInvocations"
  namespace                 = "AWS/Events"
  period                    = "300"
  statistic                 = "Sum"
  threshold                 = "1"
  treat_missing_data        = "notBreaching"
  alarm_description         = "Alerts if EventBridge fails to publish a cron event to lambda"
  alarm_actions             = [aws_sns_topic.alarms.arn]
  insufficient_data_actions = [aws_sns_topic.alarms.arn]
  ok_actions                = [aws_sns_topic.alarms.arn]

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.cron.name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_dead_letter_queue_items" {
  alarm_name                = "${aws_sqs_queue.lambda_dead_letter_queue.name} items"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "1"
  metric_name               = "ApproximateNumberOfMessagesVisible"
  namespace                 = "AWS/SQS"
  period                    = "300"
  statistic                 = "Maximum"
  threshold                 = "1"
  treat_missing_data        = "ignore" # Maintain alarm state on missing data - sometimes data will just be missing for queues for some reason
  alarm_description         = "Alerts if the lambda dead-letter queue has items in it"
  alarm_actions             = [aws_sns_topic.alarms.arn]
  insufficient_data_actions = [aws_sns_topic.alarms.arn]
  ok_actions                = [aws_sns_topic.alarms.arn]

  dimensions = {
    QueueName = aws_sqs_queue.lambda_dead_letter_queue.name
  }
}
