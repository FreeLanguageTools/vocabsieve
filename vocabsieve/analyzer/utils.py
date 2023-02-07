import os
from lxml import etree
from bs4 import BeautifulSoup
from charset_normalizer import from_bytes
from collections import Counter
from operator import itemgetter
from ebooklib import epub, ITEM_DOCUMENT
import mobi

