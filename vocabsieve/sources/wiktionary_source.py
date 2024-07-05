import requests
from bs4 import BeautifulSoup
from ..models import DictionarySource, SourceOptions, LookupResult
from loguru import logger
import json
from ..cached_get import cached_get
from ..dictformats import kaikki_line_to_textdef
from ..constants import langcodes


class WiktionarySource(DictionarySource):
    def __init__(self, langcode: str, options: SourceOptions) -> None:
        # Wiktionary lists all Bosnian, Croatian, Serbian as "sh" (Serbo-Croatian)
        # We need to map this to the correct language code
        if langcode in ["sr", "hr", "bs"]:
            langcode = "sh"
        super().__init__("Wiktionary (English)", langcode, options)

    def _lookup(self, word: str) -> LookupResult:
        logger.info(f"Looking up {word} in Wiktionary")
        language_longname = langcodes[self.langcode]
        try:
            res = cached_get(
                f"https://kaikki.org/dictionary/{language_longname}/meaning/{word[0]}/{word[0:2]}/{word}.jsonl")
        except Exception as e:
            logger.error(f"Failed to get data from Wiktionary: {repr(e)}")
            return LookupResult(error=repr(e))
        if res.status_code != 200:
            return LookupResult(error=str(res.text))
        datalines = res.content.decode('utf-8').splitlines()
        items: list[str] = []
        for line in datalines:
            data = json.loads(line)
            items.append(kaikki_line_to_textdef(data))
        if items:
            return LookupResult(definition="<br>\n".join(items))
        else:
            return LookupResult(error="No definitions found")
