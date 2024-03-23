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


def modifier_threshold_display(modifier: float, threshold: int) -> str:
    if modifier == 1.0:
        return f"{threshold}"
    else:
        return f"<b>{int(threshold * modifier)}</b>"


class WordRecordDisplay(QLabel):
    def __init__(self):
        super().__init__()
        self.setToolTip(
            """Total score / Threshold
Bolded threshold means that the word is marked manually
S: times seen
L: times looked up
T: number of mature anki cards as word
t: number of young anki cards as word
C: number of mature anki cards as context
c: number of young anki cards as context
Weights can be changed in the Tracking tab"""
        )

    def setWordRecord(self, wr: WordRecord, waw: WordActionWeights, threshold: int, modifier: float):
        score = compute_word_score(wr, waw)
        if (score > 0):
            self.setText(
                f"{score}/{modifier_threshold_display(modifier, threshold)} "
                f"({pretty_symbol_display('S', wr.n_seen)}"
                f"{pretty_symbol_display('L', wr.n_lookups)}"
                f"{pretty_symbol_display('T', wr.anki_mature_tgt)}"
                f"{pretty_symbol_display('C', wr.anki_mature_ctx)}"
                f"{pretty_symbol_display('t', wr.anki_young_tgt)}"
                f"{pretty_symbol_display('c', wr.anki_young_ctx)}".strip() + ")"
            )
        else:
            self.setText("new word")
