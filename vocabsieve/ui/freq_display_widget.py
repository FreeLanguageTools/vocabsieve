from PyQt5.QtWidgets import QLineEdit
from ..models import FreqSource
from typing import Optional

class FreqDisplayWidget(QLineEdit):
    def __init__(self):
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

    def lookup(self, word: str):
        self.setText(str(self.getFreq(word)))