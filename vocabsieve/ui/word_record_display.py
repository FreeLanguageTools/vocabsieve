from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLabel
from ..models import WordRecord




class WordRecordDisplay(QLabel):
    def __init__(self):
        super().__init__()

    def setWordRecord(self, wr: WordRecord):
        self.setText(
            f"S:{wr.n_seen} L:{wr.n_lookups} A: {'T'*wr.anki_mature_tgt + 't'*wr.anki_young_tgt + 'C'*(wr.anki_mature_ctx) + 'c'*(wr.anki_young_ctx)}"
        )