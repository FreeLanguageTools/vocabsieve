from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLabel
from ..models import WordActionWeights, WordRecord
from ..tools import compute_word_score


def pretty_symbol_display(symbol: str, number: int) -> str:
    if number == 0:
        return ""
    if number == 1:
        return f"{symbol} "
    if number > 1:
        return f"{number}{symbol} "
    return ""

class WordRecordDisplay(QLabel):
    def __init__(self):
        super().__init__()

    def setWordRecord(self, wr: WordRecord, waw: WordActionWeights):
        self.setText(
            f"{compute_word_score(wr, waw)} "
            f"({pretty_symbol_display('S', wr.n_seen)}"
            f"{pretty_symbol_display('L', wr.n_lookups)}" 
            f"{pretty_symbol_display('T', wr.anki_mature_tgt)}"
            f"{pretty_symbol_display('C', wr.anki_mature_ctx)}"
            f"{pretty_symbol_display('t', wr.anki_young_tgt)}"
            f"{pretty_symbol_display('c', wr.anki_young_ctx)}".strip() + ")"
        )