import requests
from bs4 import BeautifulSoup
from ..models import DictionarySource, SourceOptions, LookupResult
from loguru import logger
from ..cached_get import cached_get


def fmt_result(definitions):
    "Format the result of dictionary lookup"
    lines = []
    for defn in definitions:
        if defn['pos'] != "":
            lines.append("<i>" + defn['pos'] + "</i>")
        lines.extend([str(item[0] + 1) + ". " + item[1]
                     for item in list(enumerate(defn['meaning']))])
    return "<br>".join(lines)


class WiktionarySource(DictionarySource):
    def __init__(self, langcode: str, options: SourceOptions) -> None:
        # Wiktionary lists all Bosnian, Croatian, Serbian as "sh" (Serbo-Croatian)
        # We need to map this to the correct language code
        if langcode in ["sr", "hr", "bs"]:
            langcode = "sh"
        super().__init__("Wiktionary (English)", langcode, options)

    def _lookup(self, word: str) -> LookupResult:
        logger.info(f"Looking up {word} in Wiktionary")
        try:
            res = cached_get(
                'https://en.wiktionary.org/api/rest_v1/page/definition/' +
                word)
        except Exception as e:
            logger.error(f"Failed to get data from Wiktionary: {repr(e)}")
            return LookupResult(error=str(e))
        if res.status_code != 200:
            return LookupResult(error=str(res.text))
        definitions = []
        data = res.json()
        if self.langcode not in data.keys():
            return LookupResult(error="Word not defined in language")
        data = data[self.langcode]
        for item in data:
            meanings = []
            for defn in item['definitions']:
                parsed_meaning = BeautifulSoup(defn['definition'], features="lxml")
                meanings.append(parsed_meaning.text)

            meaning_item = {"pos": item['partOfSpeech'], "meaning": meanings}
            definitions.append(meaning_item)
        return LookupResult(definition=fmt_result(definitions))
