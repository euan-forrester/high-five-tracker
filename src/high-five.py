#!/usr/bin/env python3

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import logging
import sys
import json
import re
import spacy
from bs4 import BeautifulSoup
from datetime import datetime

from confighelper import ConfigHelper

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

BASE_URL                = config_helper.get("base-url")
BATCH_SIZE              = config_helper.getInt("batch-size")
NUM_RETRIES             = config_helper.getInt("num-retries")
RETRY_BACKOFF_FACTOR    = config_helper.getFloat("retry-backoff-factor")

NAMES_OF_INTEREST       = config_helper.getArray("names-of-interest")
COMMUNITIES_OF_INTEREST = config_helper.getArray("communities-of-interest")

TARGET_EMAIL_ADDRESS    = config_helper.get("target-email")#, is_secret=True)
FROM_EMAIL_ADDRESS      = config_helper.get("from-email")#, is_secret=True)

NAMES_OF_INTEREST_LOWERCASE = [s.lower() for s in NAMES_OF_INTEREST]
COMMUNITIES_OF_INTEREST_LOWERCASE = [s.lower() for s in COMMUNITIES_OF_INTEREST]

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("en_core_web_sm")

def sanitize_string(s):
  if s is None:
    return None

  s = s.strip()
  s = re.sub(r'[^\x20-\x7E]', '', s)
  return s

def parse_date(s):
  if s is None:
    return None

  return datetime.strptime(s, '%b %d, %Y') # Example date is 'Apr 27, 2023'

def parse_high_five(i):
  soup = BeautifulSoup(i['Html'], 'html.parser')  

  card_div = soup.find('div', {'class': 'highfive-card'})

  community_div = card_div.find('span', {'class': 'field-communityname'}) if card_div is not None else None
  community_text = community_div.text if community_div is not None else None

  message_div = card_div.find('div', {'class': 'field-message'}) if card_div is not None else None
  message_text = message_div.text if message_div is not None else None

  date_div = card_div.find('div', {'class': 'field-highfivedate'}) if card_div is not None else None
  date_text = date_div.text if date_div is not None else None

  firstname_div = card_div.find('div', {'class': 'field-firstname'}) if card_div is not None else None
  firstname_text = firstname_div.text if firstname_div is not None else None

  return {
    'id': i['Id'],
    'date': parse_date(sanitize_string(date_text)),
    'name': sanitize_string(firstname_text),
    'community': sanitize_string(community_text),
    'message': sanitize_string(message_text)
  }

def high_five_has_name_of_interest(high_five):
  for name in NAMES_OF_INTEREST_LOWERCASE:
    if name in high_five['message'].lower():
      if (high_five['community'] is None) or (high_five['community'].lower() in COMMUNITIES_OF_INTEREST_LOWERCASE):
        logger.info(f"Found {name} in {high_five['community']}")
        return True

  return False

def get_all_people_from_high_five(high_five):
  document = nlp(high_five['message'])

  person_entities = list(filter(lambda entity:entity.label_ == 'PERSON', document.ents))
  person_names = list(map(lambda entity:entity.text, person_entities))

  person_names_deduplicated = list(set(person_names))

  return person_names_deduplicated

def print_high_five(high_five):
  logger.info(f"Date: {high_five['date'].strftime('%b %-d, %Y')}") if high_five['date'] is not None else None
  logger.info(f"From: {high_five['name']}") if high_five['name'] is not None else None
  logger.info(f"Community: {high_five['community']}") if high_five['community'] is not None else None
  logger.info(f"Message: {high_five['message']}")

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

    high_fives_batch = list(map(parse_high_five, response_data['Results']))
    high_fives_batch = list(filter(lambda high_five:high_five['message'] is not None, high_fives_batch))

    all_high_fives += high_fives_batch

    if current_offset >= total_high_fives:
      break

  return all_high_fives

def get_person_in_community_counts(high_fives):
  person_counts = {}

  for high_five in all_high_fives:
    new_people = get_all_people_from_high_five(high_five)

    if len(new_people) == 0:
      continue

    community = high_five['community']

    if community not in person_counts:
      person_counts[community] = {}

    for person in new_people:
      if person not in person_counts[community]:
        person_counts[community][person] = 1
      else:
        person_counts[community][person] += 1
  
  return person_counts

def sort_person_in_community_counts(person_counts):
  sorted_person_counts = {}

  for community in person_counts.keys():
    sorted_person_counts[community] = dict(sorted(person_counts[community].items(), key=lambda x: x[1], reverse=True))    

  return sorted_person_counts

def get_new_high_fives_and_send_email(event, context):
  # Request all of the high fives and filter out the ones that contain our person and community of interest

  all_high_fives = get_all_high_fives()

  interesting_high_fives = list(filter(high_five_has_name_of_interest, all_high_fives))

  '''
  person_counts = get_person_in_community_counts(all_high_fives)
  sorted_person_counts = sort_person_in_community_counts(person_counts)

  for community, person_counts in sorted_person_counts.items():
    print("\n")
    for person_name, count in person_counts.items():
      print(f"Name: {person_name}, Community: {community} Total high fives: {count}")
  '''

  logger.info(f"Found {len(interesting_high_fives)} interesting high fives")
  for high_five in interesting_high_fives:
    logger.info("\n\n")
    print_high_five(high_five)
