from vocabsieve.db import LocalDictionary
from ..models import Source, Definition, LemmaPolicy
from ..db import LocalDictionary

class LocalSource(Source):
    def __init__(self, langcode: str, lemma_policy: LemmaPolicy, db: LocalDictionary) -> None:
        super().__init__("Local", langcode, lemma_policy)
        self.db = db

    def _lookup(self, word: str) -> Definition:
        definition = self.db.define(word, self.langcode, self.name)
        return Definition(headword=word, source=self.name, definition=definition)