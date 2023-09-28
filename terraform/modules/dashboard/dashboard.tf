resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_dashboards ? 1 : 0 # Don't create this if we turn off dashboards (e.g. for dev). We only get a few dashboards in total at the AWS Free Tier

  dashboard_name = "${var.application_name}-${var.environment}"

  dashboard_body = <<EOF
  {
    "widgets": [
       {
          "x":0,
          "y":0,
          "width":24,
          "height":6,
          ${data.template_file.most_recent_high_five_age_days.rendered}
       },
       {
          "x":0,
          "y":6,
          "width":24,
          "height":6,
          ${data.template_file.total_high_fives.rendered}
       },
       {
          "x":0,
          "y":6,
          "width":12,
          "height":6,
          ${data.template_file.eventbridge_failed_invocations.rendered}
       },
       {
          "x":12,
          "y":6,
          "width":12,
          "height":6,
          ${data.template_file.dead_letter_queue_items.rendered}
       }
    ]
  }
  
EOF

}

data "template_file" "most_recent_high_five_age_days" {
  vars = {
    metrics_namespace = var.metrics_namespace
    environment       = var.environment
    region            = var.region
  }

  template = file("${path.module}/most_recent_high_five_age_days.tpl")
}

data "template_file" "total_high_fives" {
  vars = {
    metrics_namespace = var.metrics_namespace
    environment       = var.environment
    region            = var.region
  }

  template = file("${path.module}/total_high_fives.tpl")
}

data "template_file" "eventbridge_failed_invocations" {
  vars = {
    rule_name         = var.cloudwatch_event_rule_cron_name
    region            = var.region
  }

  template = file("${path.module}/eventbridge_failed_invocations.tpl")
}

data "template_file" "dead_letter_queue_items" {
  vars = {
    queue_name        = var.lamdba_dead_letter_queue_name
    region            = var.region
  }

  template = file("${path.module}/dead_letter_queue_items.tpl")
}
