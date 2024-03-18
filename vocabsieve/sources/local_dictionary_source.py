from ..models import DictionarySource, SourceOptions, LookupResult
from ..local_dictionary import dictdb


class LocalDictionarySource(DictionarySource):
    INTERNET = False

    def __init__(self, langcode: str, options: SourceOptions, dictname: str) -> None:
        super().__init__(dictname, langcode, options)
        # Ensure dictname exists in db

    def _lookup(self, word: str) -> LookupResult:
        try:
            definition = dictdb.define(word, self.langcode, self.name)
            return LookupResult(definition=definition)
        except KeyError as e:
            print(repr(e))
            return LookupResult(error=repr(e))
