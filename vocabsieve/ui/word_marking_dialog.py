from PyQt5.QtWidgets import QVBoxLayout, QDialog, QLabel, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt


from ..models import WordRecord
from .main_window_base import MainWindowBase
from ..tools import compute_word_score
from ..global_names import settings, logger

class TogglableLabel(QLabel):
    def __init__(self, parent: "WordGridWidget"):
        super().__init__()
        self.parent_ = parent
        self.rec = parent.rec # type: ignore
        self.langcode = settings.value("target_language", "en")
        self.mousePressEvent = self.onClicked
        self.word = ""

    def setText(self, text: str):
        self.score = compute_word_score(self.parent_.known_data.get(text, WordRecord(text, self.langcode)), self.parent_.waw) # type: ignore
        self.threshold: int = settings.value("tracking/known_threshold", 100, type=int) if text not in self.parent_.cognates else settings.value("tracking/known_threshold_cognate", 25, type=int) # type: ignore
        self.modifier: float = self.rec.getModifier(self.langcode, text)
        self.known = False
        stylesheet = "border: 2px solid transparent; border-radius: 5px; padding: 4px;"
        if self.score >= self.threshold * self.modifier:
            stylesheet += "background-color: rgba(50,205,50,0.6);"
            self.known = True
            if self.modifier != 1.0:
                stylesheet += "border: 2px solid transparent; font-weight: bold; text-decoration: underline;" # Overridden as known: bold and underline
        else:
            if self.modifier != 1.0:
                stylesheet += "border: 2px solid rgb(220,20,60); font-weight: bold; text-decoration: underline;" # Overridden as unknown: bold underline and red border
        self.setStyleSheet(stylesheet)
        self.word = text
        super().setText((text + f" ({self.score}/{int(self.threshold * self.modifier)})") if text else "")
    
    def onClicked(self, ev: QMouseEvent):
        if not self.word:
            return
        logger.debug(f"User pressed on {self.word} in mark words dialog")
        if self.modifier == 1.0:
        # Set modifier
            if self.known:
                self.modifier = self.score / self.threshold * 2
                self.rec.setModifier(self.langcode, self.word, self.modifier)
                logger.info(f"Seting modifier of {self.word} to {self.modifier} (as unknown)")
            else:
                self.modifier = 0.0
                self.rec.setModifier(self.langcode, self.word, self.modifier)
                logger.info(f"Seting modifier of {self.word} to {self.modifier} (as known)")
        else:
        # Reset modifier
            self.modifier = 1.0
            self.rec.setModifier(self.langcode, self.word, self.modifier)
            logger.info(f"Resetting modifier of {self.word} to {self.modifier}")

        self.setText(self.word)
        
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
        self.known_data, _ = parent.rec.getKnownData()
        self.layout_ = QGridLayout(self)
        self.index_offset_label = QLabel("<b>Rank 0</b>")
        self.layout_.addWidget(self.index_offset_label, 0, 0, 1, COLS-2)
        self.reset_button = QPushButton("Reset all modifiers to default")
        self.reset_button.clicked.connect(self.resetModifiers)
        self.layout_.addWidget(self.reset_button, 0, COLS-2, 1, 2)
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

    def resetModifiers(self):
        logger.info("Resetting all modifiers to default by user request")
        self.rec.deleteModifiers(settings.value("target_language", "en"))
        self.update()
    



class WordMarkingDialog(QDialog):
    def __init__(self, parent: MainWindowBase, words: list[str] = []):
        super().__init__(parent)
        self.setWindowTitle("Mark words from frequency list")
        self.resize(1200, 700)
        self.rec = parent.rec
        langcode = settings.value("target_language", "en")
        known_langs = settings.value('tracking/known_langs', 'en').split(",")
        self.cognates = parent.dictdb.getCognatesData(langcode, known_langs)
        self.waw = parent.getWordActionWeights()
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(QLabel("Click on a word to toggle its known status. Clicking again resets the modifier to default. <br> Modified words are displayed in bold and underlined. Changes are saved automatically to the database."))

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

        