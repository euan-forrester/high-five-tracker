import sys
sys.path.append("../src")

from highfiveparser import HighFiveParser

def test_single_community():
  high_five_obj = {
    "Id": "556f6b73-fb80-4562-854c-90c1bd4eaac0",
    "Language": "en",
    "Path": "/sitecore/content/FraserHealth/FraserHealth/Home/highfive/2023/high-five-8",
    "Url": "https://www.fraserhealth.ca/highfive/2023/high-five-8",
    "Name": None,
    "Html": "<div class=\"highfive-card\"><div class=\"card-message-wrapper\"><div class=\"highfive-community\"><span class=\"community-label\">For</span><span class=\"field-communityname\">Maple Ridge</span></div><div class=\"field-message\">The nurses, physician and other staff made my young daughter and I feel taken care of. While chatting with us, the friendly greeter gave my child a goodie bag with toys and activities. The sweet discharge nurse gave her a Popsicle, and the attending doctor was caring and kind. Absolutely over and above any hospital visit I've ever had. Thank you to the staff for being kind and making an ill little girl feel better.</div><div class=\"field-highfivedate\">Sep 15, 2023</div><div class=\"field-firstname\">Samantha Johnstone </div></div></div>"
  }

  high_five = HighFiveParser.parse_high_five(high_five_obj)

  assert high_five['id'] == "556f6b73-fb80-4562-854c-90c1bd4eaac0"
  assert HighFiveParser.stringify_date(high_five['date']) == "Sep 15, 2023"
  assert high_five['name'] == "Samantha Johnstone"
  assert high_five['community'] == "Maple Ridge"
  assert high_five['message'] == "The nurses, physician and other staff made my young daughter and I feel taken care of. While chatting with us, the friendly greeter gave my child a goodie bag with toys and activities. The sweet discharge nurse gave her a Popsicle, and the attending doctor was caring and kind. Absolutely over and above any hospital visit I've ever had. Thank you to the staff for being kind and making an ill little girl feel better."
    