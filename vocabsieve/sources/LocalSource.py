from vocabsieve.db import LocalDictionary
from ..models import Source, SourceOptions, LookupResult
from ..db import LocalDictionary

class LocalSource(Source):
    def __init__(self, langcode: str, options: SourceOptions, db: LocalDictionary) -> None:
        super().__init__("Local", langcode, options)
        self.db = db

    def _lookup(self, word: str) -> LookupResult:
        definition = self.db.define(word, self.langcode, self.name)
        return LookupResult(definition=definition)