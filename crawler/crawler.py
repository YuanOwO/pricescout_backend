import csv
import json
import os
import re
from decimal import Decimal

import requests

from . import CR4_Crawler, PX_Crawler
from .config import DEFAULT_HEADER

with PX_Crawler() as crawler:
    crawler.get_all_products()

with CR4_Crawler() as crawler:
    crawler.get_all_products()


# url = 'https://tw.fd-api.com/api/v5/graphql'

# resp = requests.post(url, json=data, headers=DEFAULT_HEADER)


# with open('fd.json', 'w', encoding='utf-8') as f:
#     json.dump(resp.json(), f, ensure_ascii=False, indent=4)
