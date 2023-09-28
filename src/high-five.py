#!/usr/bin/env python3

import sys
sys.path.insert(0, './common')

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import boto3
from botocore.exceptions import ClientError

import logging
import sys
import json
from datetime import date

from highfiveparser import HighFiveParser
from confighelper import ConfigHelper
from metricshelper import MetricsHelper

#
# Setup logging
#

if logging.getLogger().hasHandlers():
  # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
  # `.basicConfig` does not execute. Thus we set the level directly.
  logging.getLogger().setLevel(logging.INFO)
else:
  logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()

#
# Get our config
#

config_helper = ConfigHelper.get_config_helper(default_env_name="dev", application_name="high-five-tracker")

AWS_REGION              = config_helper.get("aws-region")

BASE_URL                = config_helper.get("base-url")
BATCH_SIZE              = config_helper.getInt("batch-size")
NUM_RETRIES             = config_helper.getInt("num-retries")
RETRY_BACKOFF_FACTOR    = config_helper.getFloat("retry-backoff-factor")

NAMES_OF_INTEREST       = config_helper.getArray("names-of-interest")
COMMUNITIES_OF_INTEREST = config_helper.getArray("communities-of-interest")

RUN_AT_SCRIPT_STARTUP   = config_helper.getBool("run-at-script-startup")

METRICS_NAMESPACE       = config_helper.get("metrics-namespace")
SEND_METRICS            = config_helper.getBool("send-metrics")

CHECK_DATABASE          = config_helper.getBool("check-database")

SEND_EMAIL              = config_helper.getBool("send-email")
SUBJECT_LINE_SINGULAR   = config_helper.get("subject-line-singular")
SUBJECT_LINE_PLURAL     = config_helper.get("subject-line-plural")
TO_EMAIL_ADDRESS        = config_helper.get("to-email")
CC_EMAIL_ADDRESS        = config_helper.get("cc-email")
FROM_EMAIL_ADDRESS      = config_helper.get("from-email")

NAMES_OF_INTEREST_LOWERCASE = [s.lower() for s in NAMES_OF_INTEREST]
COMMUNITIES_OF_INTEREST_LOWERCASE = [s.lower() for s in COMMUNITIES_OF_INTEREST]

#
# Init AWS stuff
#

ses = boto3.client('ses', region_name=AWS_REGION)
metrics_helper = MetricsHelper(environment=config_helper.get_environment(), region=AWS_REGION, metrics_namespace=METRICS_NAMESPACE)

#
# Helper functions
#

def high_five_has_name_of_interest(high_five):
  for name in NAMES_OF_INTEREST_LOWERCASE:
    if name in high_five['message'].lower():
      community_matches = False

      if len(high_five['communities']) == 0:
        logger.info(f"No community specified in High Five, so found name {name} by default")
        community_matches = True

      for community_name in high_five['communities']:
        if community_name.lower() in COMMUNITIES_OF_INTEREST_LOWERCASE:
          logger.info(f"Found {name} in {community_name}")
          community_matches = True
          break

      return community_matches

  return False

def get_all_high_fives():
  retries = Retry(total=NUM_RETRIES, backoff_factor=RETRY_BACKOFF_FACTOR)
  adapter = HTTPAdapter(max_retries=retries)

  session = requests.Session()
  session.mount("https://", adapter)

  # The pagination of this endpoint is a bit strange
  #
  # We can't just keep going until we get no results, because there is a point near the end of the results where we can get an
  # empty response, but if we keep going we will eventially find more.
  #
  # There's a Count value in the object returned, and it seems to fluctuate between 2 or more values as we page through the
  # results. My guess is that it's fluctuating between the actual number of real records, and the largest ID of a record -- since there's the gap mentioned above.
  #
  # So, we're going to keep track of the largest count that we see, and keep asking for results until we hit it

  current_offset = 0
  total_high_fives = 0

  all_high_fives = []

  while True:
    # p is the count
    # e is the offset
    url = BASE_URL + f"&p={BATCH_SIZE}&e={current_offset}"

    response = session.get(url)

    if response.status_code != 200:
      logger.error(f"Received status code {response.status_code} after {REQUEST_RETRIES} attempts from URL '{url}'")
      sys.exit(-1)

    response_data = json.loads(response.text)

    total_high_fives = max(total_high_fives, response_data['Count'])

    current_offset += BATCH_SIZE

    high_fives_batch = list(map(HighFiveParser.parse_high_five, response_data['Results']))
    high_fives_batch = list(filter(lambda high_five:high_five['message'] is not None, high_fives_batch))

    all_high_fives += high_fives_batch

    if current_offset >= total_high_fives:
      break

  return all_high_fives

def email_high_fives(high_fives):
  body_text = "\n\n".join(map(HighFiveParser.stringify_high_five, high_fives))

  subject_line = SUBJECT_LINE_SINGULAR

  if len(high_fives) > 1:
    subject_line = SUBJECT_LINE_PLURAL.format(len(high_fives))

  # Object structure described at https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses/client/send_email.html#
  send_args = {
    'Source': FROM_EMAIL_ADDRESS,
    'Destination': {
      'ToAddresses': [TO_EMAIL_ADDRESS],
    },
    'Message': {
      'Subject': {'Data': subject_line},
      'Body': {'Text': {'Data': body_text}}
    }
  }
  if CC_EMAIL_ADDRESS is not None:
    send_args['Destination']['CcAddresses'] = [CC_EMAIL_ADDRESS]

  try:
    response = ses.send_email(**send_args)
    message_id = response['MessageId']
    logger.info(f"Successfully sent mail '{message_id}' from '{FROM_EMAIL_ADDRESS}' to '{TO_EMAIL_ADDRESS}'")
  except ClientError:
    logger.exception(f"Could not send mail from '{FROM_EMAIL_ADDRESS}' to '{TO_EMAIL_ADDRESS}'")
    raise

def calculate_metrics(high_fives):
  logger.info("*** Metrics information ***")
  num_high_fives_found = len(high_fives)

  logger.info(f"Found {num_high_fives_found} total High Fives")

  if num_high_fives_found == 0:
    logger.info("No high fives found, so no further telemetry can be sent")
    return

  most_recent_high_five = high_fives[0]

  if most_recent_high_five['date'] is None:
    logger.info(f"No date found in High Five {most_recent_high_five['id']} so can't send telemetry about its age")
  else:
    most_recent_high_five_age_days = (date.today() - most_recent_high_five['date']).days
    logger.info(f"Most recent High Five found is {most_recent_high_five_age_days} days old")

  if SEND_METRICS:
    metrics_helper.send_count("total-high-fives", num_high_fives_found)
    metrics_helper.send_count("most-recent-high-five-age-days", most_recent_high_five_age_days)

def log_high_five(high_five):
  high_five_components = HighFiveParser.stringify_high_five_components(high_five)

  for component in high_five_components:
    logger.info(component)

def get_new_high_fives_and_send_email(event, context):
  # Request all of the high fives and filter out the ones that contain our person and community of interest

  all_high_fives = get_all_high_fives()

  interesting_high_fives = list(filter(high_five_has_name_of_interest, all_high_fives))

  logger.info(f"Found {len(interesting_high_fives)} interesting high fives")
  for high_five in interesting_high_fives:
    logger.info("\n\n")
    log_high_five(high_five)

  if SEND_EMAIL:
    email_high_fives(interesting_high_fives)

  calculate_metrics(all_high_fives)

if RUN_AT_SCRIPT_STARTUP:
  get_new_high_fives_and_send_email(None, None)