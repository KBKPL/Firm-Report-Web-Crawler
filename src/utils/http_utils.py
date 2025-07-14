"""
HTTP utilities: session with retries for robust HTTP requests.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session():
    s = requests.Session()
    # Set a browser-like User-Agent to avoid 403 errors
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'})
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

session = create_session()
