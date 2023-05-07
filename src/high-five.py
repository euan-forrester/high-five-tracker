#!/usr/bin/env python3

import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

NAMES_OF_INTEREST = [ 'Katie', 'Toews' ]

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

def parse_response_item(i):
  soup = BeautifulSoup(i['Html'], 'html.parser')  

  card_div = soup.find('div', {'class': 'highfive-card'})

  community_div = card_div.find('span', {'class': 'field-communityname'})
  community_text = community_div.text if community_div is not None else None

  message_div = card_div.find('div', {'class': 'field-message'})
  message_text = message_div.text if message_div is not None else None

  date_div = card_div.find('div', {'class': 'field-highfivedate'})
  date_text = date_div.text if date_div is not None else None

  firstname_div = card_div.find('div', {'class': 'field-firstname'})
  firstname_text = firstname_div.text if firstname_div is not None else None

  return {
    'id': i['Id'],
    'date': parse_date(sanitize_string(date_text)),
    'first_name': sanitize_string(firstname_text),
    'community': sanitize_string(community_text),
    'message': sanitize_string(message_text)
  }

def high_five_has_name_of_interest(high_five):
  for name in NAMES_OF_INTEREST:
    if name.lower() in high_five['message'].lower():
      return True

  return False

url = "https://www.fraserhealth.ca//sxa/search/results/?l=en&s={8A83A1F3-652A-4C01-B247-A2849DDE6C73}&sig=&defaultSortOrder=HighFiveDate,Descending&.ZFZ0zOzMLUY=null&v={C0113845-0CB6-40ED-83E4-FF43CF735D67}&p=1000&o=HighFiveDate,Descending&site=null"

response = requests.get(url)

response_data = json.loads(response.text)

response_count = response_data['Count']

all_high_fives = list(map(parse_response_item, response_data['Results']))

interesting_high_fives = list(filter(high_five_has_name_of_interest, all_high_fives))

print(interesting_high_fives)