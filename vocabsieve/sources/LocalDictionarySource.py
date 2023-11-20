from vocabsieve.db import LocalDictionary
from ..models import DictionarySource, SourceOptions, LookupResult
from ..db import LocalDictionary

class LocalDictionarySource(DictionarySource):
    def __init__(self, langcode: str, options: SourceOptions, db: LocalDictionary, dictname: str) -> None:
        super().__init__(dictname, langcode, options)
        self.db = db
        # Ensure dictname exists in db

    def _lookup(self, word: str) -> LookupResult:
        try:
            print("Looking up", word, "in", self.name)
            definition = self.db.define(word, self.langcode, self.name)
            print("Definition:", definition)
            return LookupResult(definition=definition)
        except TypeError as e:
            print("Word not found")
            return LookupResult(error="Word not found")