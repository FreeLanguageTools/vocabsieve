from functools import lru_cache
import requests
from .constants import FORVO_HEADERS


@lru_cache(maxsize=5000)
def cached_get(url, forvo_headers=False):
    """
    Cached requests.get
    Note this will throw an exception, which is not cached
    """
    if forvo_headers:
        res = requests.get(url, headers=FORVO_HEADERS, timeout=10)
    else:
        res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res
