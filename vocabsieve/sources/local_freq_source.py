from ..models import FreqSource
from ..local_dictionary import LocalDictionary


class LocalFreqSource(FreqSource):
    INTERNET = False

    def __init__(self, langcode: str, lemmatized: bool, db: LocalDictionary, dictname: str) -> None:
        super().__init__(dictname, langcode, lemmatized)
        self.db = db

    def _lookup(self, word: str) -> int:
        try:
            return int(self.db.define(word, self.langcode, self.name))
        except KeyError:
            return -1

    def getAllWords(self) -> list[str]:
        data = self.db.getAllWords(self.langcode, self.name)
        d = {int(data[i][1]): data[i][0] for i in range(len(data))}
        return [d[i] for i in sorted(d.keys())]
