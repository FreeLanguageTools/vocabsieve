import requests
from bs4 import BeautifulSoup
from ..models import DictionarySource, SourceOptions, LookupResult

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
        super().__init__("Wiktionary (English)", langcode, options)

    def _lookup(self, word: str) -> LookupResult:
        try:
            res = requests.get(
                'https://en.wiktionary.org/api/rest_v1/page/definition/' +
                word,
                timeout=4)
        except Exception as e:
            return LookupResult(error=str(e))

        if res.status_code != 200:
            raise Exception("Lookup error")
        definitions = []
        data = res.json()[self.langcode]
        for item in data:
            meanings = []
            for defn in item['definitions']:
                parsed_meaning = BeautifulSoup(defn['definition'], features="lxml")
                meanings.append(parsed_meaning.text)

            meaning_item = {"pos": item['partOfSpeech'], "meaning": meanings}
            definitions.append(meaning_item)
        return LookupResult(definition=fmt_result(definitions))

