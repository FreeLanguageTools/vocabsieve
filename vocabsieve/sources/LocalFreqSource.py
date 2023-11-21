from ..models import FreqSource
from ..local_dictionary import LocalDictionary

class LocalFreqSource(FreqSource):
    def __init__(self, langcode: str, lemmatized: bool, db: LocalDictionary, dictname: str) -> None:
        super().__init__(dictname, langcode, lemmatized)
        self.db = db

    def _lookup(self, word: str) -> int:
        try:
            return int(self.db.define(word, self.langcode, self.name))
        except KeyError:
            return -1