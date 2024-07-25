import hashlib
from datetime import datetime

read_timeout = 10
dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'


def url_headers(referer="https://www.google.com/"):
    """
    Returns the headers dictionary with User-Agent, Accept-Encoding, Accept-Language, Referer, and Accept values.

    Parameters:
        referer (str, optional): The referer URL. Defaults to "https://www.google.com/".

    Returns:
        dict: A dictionary containing the headers.
    """
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
    """
    Converts a given date string to a formatted date string.

    Args:
        date (str): The date string to be converted. The date string should be in the format "%A, %B %d, %Y".

    Returns:
        str: The formatted date string. The format of the date string is determined by the `dateformat` variable.
    """
    datetime_obj = datetime.strptime(date, "%A, %B %d, %Y")
    date_str = datetime_obj.strftime(dateformat)
    return date_str


def sha_conversion(url: str) -> str:
    """
    Compute the SHA-256 hash of a given URL string.

    Args:
        url (str): The URL string to be hashed.

    Returns:
        str: The hexadecimal representation of the SHA-256 hash.
    """
    sha256 = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return sha256
