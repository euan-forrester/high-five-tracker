#!/usr/bin/env python3

import requests
import json
import re
import spacy
from bs4 import BeautifulSoup
from datetime import datetime

# p is the count
# e is the offset
HIGH_FIVE_URL = "https://www.fraserhealth.ca//sxa/search/results/?l=en&sig=&defaultSortOrder=HighFiveDate,Descending&.ZFZ0zOzMLUY=null&v={C0113845-0CB6-40ED-83E4-FF43CF735D67}&p=10&e=10&o=HighFiveDate,Descending&site=null"

NAMES_OF_INTEREST = [ 'Katie', 'Kathryn', 'Toews' ]
COMMUNITIES_OF_INTEREST = [ 'Port Moody', 'New Westminster' ]

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
        print(f"Found {name} in {high_five['community']}")
        return True

  return False

def get_all_people_from_high_five(high_five):
  document = nlp(high_five['message'])

  person_entities = list(filter(lambda entity:entity.label_ == 'PERSON', document.ents))
  person_names = list(map(lambda entity:entity.text, person_entities))

  person_names_deduplicated = list(set(person_names))

  return person_names_deduplicated

def print_high_five(high_five):
  print(f"Date: {high_five['date'].strftime('%b %-d, %Y')}") if high_five['date'] is not None else None
  print(f"From: {high_five['name']}") if high_five['name'] is not None else None
  print(f"Community: {high_five['community']}") if high_five['community'] is not None else None
  print(f"Message: {high_five['message']}")

def get_all_high_fives():
  response = requests.get(HIGH_FIVE_URL)

  response_data = json.loads(response.text)

  response_count = response_data['Count']

  all_high_fives = list(map(parse_high_five, response_data['Results']))
  all_high_fives = list(filter(lambda high_five:high_five['message'] is not None, all_high_fives))

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

all_high_fives = get_all_high_fives()

interesting_high_fives = list(filter(high_five_has_name_of_interest, all_high_fives))

person_counts = get_person_in_community_counts(all_high_fives)
sorted_person_counts = sort_person_in_community_counts(person_counts)

for community, person_counts in sorted_person_counts.items():
  for person_name, count in person_counts.items():
    print("\n")
    print(f"Name: {person_name}, Community: {community} Total high fives: {count}")

print(f"Found {len(interesting_high_fives)} interesting high fives")
for high_five in all_high_fives:
  print("\n\n")
  print_high_five(high_five)
