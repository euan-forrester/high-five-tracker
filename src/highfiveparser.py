from bs4 import BeautifulSoup
import re
from datetime import datetime

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

class HighFiveParser:
  
  @staticmethod
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

  @staticmethod
  def stringify_high_five_components(high_five):
    components = [
      f"Date: {high_five['date'].strftime('%b %-d, %Y')}" if high_five['date'] is not None else None,
      f"From: {high_five['name']}" if high_five['name'] is not None else None,
      f"Community: {high_five['community']}" if high_five['community'] is not None else None,
      f"Message: {high_five['message']}"
    ]

    return filter(None, components)

  @staticmethod
  def stringify_high_five(high_five):
    return "\n".join(HighFiveParser.stringify_high_five_components(high_five))
