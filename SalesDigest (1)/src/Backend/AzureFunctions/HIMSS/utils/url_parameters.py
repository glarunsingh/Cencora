import hashlib
from datetime import datetime

read_timeout = 10
dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'

import logging
logger = logging.getLogger(__name__)

def url_headers(referer="https://www.google.com/"):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f'{referer}',
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7"
    }


def date_format(date):
    datetime_obj = datetime.strptime(date, "%A, %B %d, %Y")
    date_str = datetime_obj.strftime(dateformat)
    return date_str


def sha_conversion(url: str) -> str:
    sha256 = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return sha256
