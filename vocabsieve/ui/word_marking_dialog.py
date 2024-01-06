from PyQt5.QtWidgets import QVBoxLayout, QDialog, QLabel, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

from ..models import WordRecord
from .main_window_base import MainWindowBase
from ..tools import compute_word_score
from ..global_names import settings

class TogglableLabel(QLabel):
    def __init__(self, parent: "WordGridWidget"):
        super().__init__()
        self.parent_ = parent
        self.rec = parent.rec

    def setText(self, text: str):
        langcode = settings.value("target_language", "en")
        score = compute_word_score(self.parent_.known_data.get(text, WordRecord(text, langcode)), self.parent_.waw)
        threshold = settings.value("tracking/known_threshold", 100) if text not in self.parent_.cognates else settings.value("tracking/known_threshold_cognate", 25)
        super().setText(text + f" ({score}/{threshold})")
        
ROWS = 20
COLS = 5

class WordGridWidget(QWidget):
    def __init__(self, parent: "WordMarkingDialog", words: list[str] = []):
        super().__init__(parent)
        self.parent_ = parent
        self.words = words
        self.rec = parent.rec
        self.waw = parent.waw
        self.cognates = parent.cognates
        self.known_data, _ = self.rec.getKnownData()
        self.layout_ = QGridLayout(self)
        self.index_offset_label = QLabel("<b>Rank 0</b>")
        self.layout_.addWidget(self.index_offset_label, 0, 0, 1, COLS)
        self.page_size = ROWS * COLS
        self.page = 1
        self.last_page = len(self.words) // self.page_size + 1
        self.word_labels = [TogglableLabel(self) for _ in range(self.page_size)]
        for i in range(ROWS):
            for j in range(COLS):
                self.word_labels.append(self.word_labels[i*COLS+j])
                self.layout_.addWidget(self.word_labels[-1], i+1, j)
        self.update()
        
    def update(self):
        offset = (self.page - 1) * self.page_size
        self.index_offset_label.setText(f"<b>Rank {offset}</b>")
        for i in range(self.page_size):
            try:
                self.word_labels[i].setText(self.words[offset + i])
            except IndexError:
                self.word_labels[i].setText("")
        self.parent_.counter.setText(f"{self.page}/{self.last_page}")
    
    def forward(self):
        if self.page < self.last_page:
            self.page += 1
        self.update()
    
    def back(self):
        if self.page > 1:
            self.page -= 1
        self.update()

    def first(self):
        self.page = 1
        self.update()

    def last(self):
        self.page = self.last_page 
        self.update()
    



class WordMarkingDialog(QDialog):
    def __init__(self, parent: MainWindowBase, words: list[str] = []):
        super().__init__(parent)
        self.setWindowTitle("Mark words from frequency list")
        self.resize(800, 500)
        self.rec = parent.rec
        langcode = settings.value("target_language", "en")
        known_langs = settings.value('tracking/known_langs', 'en').split(",")
        self.cognates = parent.dictdb.getCognatesData(langcode, known_langs)
        self.waw = parent.getWordActionWeights()
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(QLabel("Mark the following words by clicking to toggle their known status.\nChanges are saved automatically to the database."))

        first_button = QPushButton("<<")
        prev_button = QPushButton("<")
        self.counter = QLabel("0/0")
        self.counter.setAlignment(Qt.AlignCenter)
        next_button = QPushButton(">")
        last_button = QPushButton(">>")

        self.wordgrid = WordGridWidget(self, words)
        self._layout.addWidget(self.wordgrid)
        buttons_box_widget = QWidget()
        self._layout.addWidget(buttons_box_widget)
        self._layout.addWidget(buttons_box_widget)

        buttons_box_layout = QHBoxLayout(buttons_box_widget)

        buttons_box_layout.addWidget(first_button)
        buttons_box_layout.addWidget(prev_button)
        buttons_box_layout.addWidget(self.counter)
        buttons_box_layout.addWidget(next_button)
        buttons_box_layout.addWidget(last_button)
        prev_button.clicked.connect(self.wordgrid.back)
        next_button.clicked.connect(self.wordgrid.forward)
        first_button.clicked.connect(self.wordgrid.first)
        last_button.clicked.connect(self.wordgrid.last)

        