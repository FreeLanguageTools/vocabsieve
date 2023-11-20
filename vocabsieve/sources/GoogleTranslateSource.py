from ..models import DictionarySource, LookupResult, SourceOptions
import requests
from urllib.parse import quote

class GoogleTranslateSource(DictionarySource):
    def __init__(self, langcode: str, options: SourceOptions, gtrans_api: str, gtrans_to_langcode: str) -> None:
        super().__init__("Google Translate", langcode, options)
        self.langcode = langcode
        if langcode == "he":
            langcode = "iw" # fix for hebrew language code
        self.gtrans_api = gtrans_api
        self.to_langcode = gtrans_to_langcode
        

    def _lookup(self, word: str) -> LookupResult:
        url = f"{self.gtrans_api}/api/v1/{self.langcode}/{self.to_langcode}/{quote(word)}"
        print(url)
        res = requests.get(url)
        if res.status_code == 200:
            return LookupResult(definition=res.json()['translation'])
        else:
            return LookupResult(error=f'{res.text}')