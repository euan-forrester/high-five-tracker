module "lambda" {
  source = "../modules/lambda"

  environment             = var.environment
  region                  = var.region
  application_name        = var.application_name

  num_days_to_keep_images = 7
  
  run_at_script_startup   = false
  check_database          = true

  metrics_namespace       = var.application_name
  send_metrics            = true

  send_email              = true
  system_email            = var.system_email
  subject_line_singular   = var.subject_line_singular
  subject_line_plural     = var.subject_line_plural
  to_email                = var.to_email
  cc_email                = var.cc_email
  from_email              = var.from_email
  names_of_interest       = var.names_of_interest
  communities_of_interest = var.communities_of_interest

  base_url                = "https://www.fraserhealth.ca//sxa/search/results/?l=en&s={8A83A1F3-652A-4C01-B247-A2849DDE6C73}&sig=&defaultSortOrder=HighFiveDate,Descending&.ZFZ0zOzMLUY=null&v={C0113845-0CB6-40ED-83E4-FF43CF735D67}&o=HighFiveDate,Descending&site=null"

  batch_size              = 1000
  num_retries             = 3
  retry_backoff_factor    = 0.5
}
