from unittest import result
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from .searchable_text_edit import SearchableTextEdit
from ..models import Definition, DictionarySourceGroup, DisplayMode
from ..format import markdown_nop
from typing import Optional

def sign(number):
    if number > 0:
        return 1
    elif number < 0:
        return -1
    else:
        return 0
    

class ButtonsBoxWidget(QWidget):
    scrolled = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.scrolled_amount = 0

    def wheelEvent(self, event: QWheelEvent):
        if sign(event.angleDelta().y()) != sign(self.scrolled_amount):
            self.scrolled_amount = 0
        self.scrolled_amount += event.angleDelta().y()
        if self.scrolled_amount >= 120:
            self.scrolled.emit(-1) # Scroll up = prev
            self.scrolled_amount = 0

        elif self.scrolled_amount <= -120:
            self.scrolled.emit(1) # Scroll down = next
            self.scrolled_amount = 0
        event.accept()



class MultiDefinitionWidget(SearchableTextEdit):
    def __init__(self, word_widget: Optional[QLineEdit] = None):
        super().__init__()
        self.sg = DictionarySourceGroup([])
        self.word_widget = word_widget
        self._layout = QVBoxLayout(self)
        self.definitions: list[Definition] = []
        self.currentIndex = 0
        self.currentDefinition: Optional[Definition] = None
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self._layout.setAlignment(Qt.AlignBottom)
        buttons_box_widget = ButtonsBoxWidget(self)
        self._layout.addWidget(buttons_box_widget)
        buttons_box_layout = QHBoxLayout(buttons_box_widget)
        buttons_box_widget.scrolled.connect(self.move_)


        prev_button = QPushButton("<")
        self.counter = QLabel("0/0")
        self.counter.setAlignment(Qt.AlignCenter)
        next_button = QPushButton(">")
        buttons_box_layout.addWidget(prev_button)
        buttons_box_layout.addWidget(next_button)
        buttons_box_layout.addWidget(self.counter)
        buttons_box_layout.addWidget(self.info_label)
        prev_button.clicked.connect(self.back)
        next_button.clicked.connect(self.forward)


    def setSourceGroup(self, sg: DictionarySourceGroup):
        self.sg = sg

    def getDefinitions(self, word: str, no_lemma=False) -> list[Definition]:
        """Can be used by other classes to get definitions from the source group
        filters out definitions with no definition"""

        return [defi for defi in self.sg.define(word, no_lemma=no_lemma) if defi.definition is not None]

    def lookup(self, word: str, no_lemma: bool = False) -> bool:
        self.reset()
        result = False
        for definition in self.getDefinitions(word, no_lemma):
            self.appendDefinition(definition)
            result = True
        return result


    def appendDefinition(self, definition: Definition):
        self.definitions.append(definition)
        self.updateIndex()

    def updateIndex(self):
        if not self.definitions:
            return
        self.counter.setText(f"{self.currentIndex+1}/{len(self.definitions)}")
        if defi:=self.definitions[self.currentIndex]:
            self.setCurrentDefinition(defi)

    def setCurrentDefinition(self, defi: Definition):
        self.currentDefinition = defi
        source_name = defi.source
        source = self.sg.getSource(source_name)
        if defi.definition is not None and source is not None:
            match source.display_mode:
                case DisplayMode.markdown_html | DisplayMode.html:
                    self.setHtml(defi.definition)
                case _:
                    self.setText(defi.definition)
            self.info_label.setText(f"<strong>{defi.headword}</strong> in <em>{defi.source}</em>")
            if self.word_widget:
                self.word_widget.setText(defi.headword)

    def setCurrentIndex(self, index: int):
        self.currentIndex = index
        self.updateIndex()

    def move_(self, amount: int):
        if amount > 0:
            for _ in range(amount):
                self.forward()
        else:
            for _ in range(-amount):
                self.back()

    def back(self):
        if self.currentIndex > 0:
            self.setCurrentIndex(self.currentIndex - 1)
        else: #wrap around
            self.setCurrentIndex(len(self.definitions) - 1)

    def forward(self):
        if self.currentIndex < len(self.definitions) - 1:
            self.setCurrentIndex(self.currentIndex + 1)
        else: #wrap around
            self.setCurrentIndex(0)

    def first(self):
        if self.definitions:
            self.setCurrentIndex(0)

    def last(self):
        if self.definitions:
            self.setCurrentIndex(len(self.definitions) - 1)

    def reset(self):
        self.definitions = []
        self.currentDefinition = None
        self.currentIndex = 0
        self.setText("")
        self.info_label.setText("")
        self.counter.setText("0/0")

    def process_defi_anki(self, defi: Optional[Definition] = None) -> str:
        """Process definitions before sending to Anki"""
        # Figure out display mode of current source
        if defi is not None:
            self.setCurrentDefinition(defi) # for non interactive use
        if self.currentDefinition is None:
            return self.toPlainText().replace("\n", "<br>")
        source_name = self.currentDefinition.source
        source = self.sg.getSource(source_name)
        if source is None:
            return self.toPlainText().replace("\n", "<br>")
        
        match source.display_mode:
            case DisplayMode.raw:
                return self.toPlainText().replace("\n", "<br>")
            case DisplayMode.plaintext:
                return self.toPlainText().replace("\n", "<br>")
            case DisplayMode.markdown:
                return markdown_nop(self.toPlainText())
            case DisplayMode.markdown_html:
                return markdown_nop(self.toMarkdown())
            case DisplayMode.html:
                return self.currentDefinition.definition or "" # no editing, just send the original html, using toHtml will change the html
            case _:
                raise NotImplementedError(f"Unknown display mode {source.display_mode}")
