from PyQt5.QtWidgets import QLineEdit
from ..models import FreqSource

class FreqDisplayWidget(QLineEdit):
    def __init__(self, source: FreqSource):
        super().__init__()
        self.setReadOnly(True)
        self.setMaxLength(8)
        self.setText("0")

    def lookup(self, word):
        