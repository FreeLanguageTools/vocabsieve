from PyQt5.QtWidgets import QLineEdit
from numpy import isin
from ..models import FreqSource, FreqDisplayMode
from ..sources.local_freq_source import LocalFreqSource
from typing import Optional, cast
from ..tools import freq_to_stars


class FreqDisplayWidget(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.source: Optional[FreqSource] = None
        self.setMaxLength(8)

    def setSource(self, source: FreqSource):
        self.source = source

    def getFreq(self, word: str) -> int:
        if self.source is None:
            return -2
        return self.source.define(word)

    def lookup(self, word: str, lemmatize: bool, display_mode):
        word_freq = self.getFreq(word)
        text = ""
        match display_mode:
            case FreqDisplayMode.stars:
                text = freq_to_stars(word_freq, lemmatize)
            case FreqDisplayMode.rank:
                text = str(word_freq) if word_freq > 0 else ""
            case _:
                pass
        self.setText(text)

    def getAllWords(self) -> list[str]:
        if isinstance(self.source, LocalFreqSource):
            return cast(LocalFreqSource, self.source).getAllWords()
        return []
