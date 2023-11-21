from ..models import DictionarySource, SourceOptions, LookupResult
from ..local_dictionary import LocalDictionary

class LocalDictionarySource(DictionarySource):
    def __init__(self, langcode: str, options: SourceOptions, dictdb: LocalDictionary, dictname: str) -> None:
        super().__init__(dictname, langcode, options)
        self.dictdb = dictdb
        # Ensure dictname exists in db

    def _lookup(self, word: str) -> LookupResult:
        try:
            definition = self.dictdb.define(word, self.langcode, self.name)
            return LookupResult(definition=definition)
        except KeyError as e:
            print(repr(e))
            return LookupResult(error=repr(e))