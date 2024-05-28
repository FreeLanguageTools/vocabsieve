from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, pyqtSlot

from .searchable_text_edit import SearchableTextEdit
from ..models import Definition, DisplayMode, DictionarySource
from ..tools import process_defi_anki, apply_word_rules
from loguru import logger
from typing import Optional
import time
from ..global_names import MOD


DEFAULT_PLACEHOLDER_TEXT = f"Look up a word by double clicking it or by selecting it, then pressing {MOD}+D.\nUse Shift-{MOD}+D to look up the word without lemmatization."
NEXT_DEFINITION_SCROLL_COUNT_TRANSITION_THRESHOLD = 3


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
            self.scrolled.emit(-1)  # Scroll up = prev
            self.scrolled_amount = 0

        elif self.scrolled_amount <= -120:
            self.scrolled.emit(1)  # Scroll down = next
            self.scrolled_amount = 0
        event.accept()


class LookupWorker(QObject):
    got_definitions = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, source: DictionarySource, word: str, no_lemma: bool, rules: list[tuple[str, str]]):
        super().__init__()
        self.source = source
        self.word = word
        self.no_lemma = no_lemma
        self.rules = rules

    def run(self):
        start = time.time()
        definitions = self.source.define(self.word, no_lemma=self.no_lemma)
        any_definitions = any(defi.definition is not None for defi in definitions)
        if not any_definitions and self.rules:
            logger.info(f"No definitions found for {self.word} in {self.source.name}, applying word rules")
            definitions = self.source.define(
                apply_word_rules(self.word, self.rules),
                no_lemma=self.no_lemma
            )
        self.got_definitions.emit(definitions)
        logger.debug(f"LookupWorker: looked up {self.word} in {self.source.name} in {time.time()-start:.2f} seconds")
        self.finished.emit()


class MultiDefinitionWidget(SearchableTextEdit):
    nextDefinitionScrollTransitionCounter = 0

    def __init__(self, word_widget: Optional[QLineEdit] = None):
        super().__init__()
        self.sources: list[DictionarySource] = []
        self.word_widget = word_widget
        self.current_target: str = ""
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

        self.threads: list[QThread] = []
        self.workers: list[LookupWorker] = []

    def wheelEvent(self, event):
        if len(self.sources) > 1:
            if self.verticalScrollBar().value() == self.verticalScrollBar().minimum() and event.angleDelta().y() > 0:
                self.nextDefinitionScrollTransitionCounter += 1
                if self.nextDefinitionScrollTransitionCounter > NEXT_DEFINITION_SCROLL_COUNT_TRANSITION_THRESHOLD:
                    self.back()
                    return

            elif self.verticalScrollBar().value() == self.verticalScrollBar().maximum() and event.angleDelta().y() < 0:
                self.nextDefinitionScrollTransitionCounter += 1
                if self.nextDefinitionScrollTransitionCounter > NEXT_DEFINITION_SCROLL_COUNT_TRANSITION_THRESHOLD:
                    self.forward()
                    return

            else:
                self.nextDefinitionScrollTransitionCounter = 0

        super().wheelEvent(event)

    def setSourceGroup(self, sources: list[DictionarySource]):
        self.sources = sources
        if not self.sources:
            self.setPlaceholderText(
                "Hint: No sources are set, so no lookups can be performed. Go to Configure -> Sources to add some sources.")
        else:
            self.setPlaceholderText(DEFAULT_PLACEHOLDER_TEXT)

    def lookup(self, word: str, no_lemma: bool, rules: list[tuple[str, str]]):
        self.reset()
        self.current_target = word
        logger.debug(f"Looking up {word} in {self.sources}")
        for source in self.sources:
            self._lookup_in_source(source, word, no_lemma=no_lemma, rules=rules)

    def _lookup_in_source(self, source: DictionarySource, word: str,
                          no_lemma: bool, rules: list[tuple[str, str]]) -> None:
        if source.INTERNET:
            lookup_thread = QThread()
            lookup_worker = LookupWorker(source, word, no_lemma, rules)
            lookup_worker.moveToThread(lookup_thread)
            lookup_thread.started.connect(lookup_worker.run)
            lookup_worker.got_definitions.connect(self.appendDefinition)
            lookup_worker.finished.connect(lookup_thread.quit)
            lookup_worker.finished.connect(lookup_worker.deleteLater)
            lookup_thread.finished.connect(lookup_thread.deleteLater)
            lookup_thread.start()

            # Keep references to avoid garbage collection, otherwise this crashes
            self.threads.append(lookup_thread)
            self.workers.append(lookup_worker)

        else:  # Local source, no thread
            self.appendDefinition(source.define(word, no_lemma=no_lemma))

    @pyqtSlot(list)
    def appendDefinition(self, definitions: list[Definition]):
        self.definitions.extend(definitions)
        # populate the definitions when all sources have been looked up
        if len(set(defi.source for defi in self.definitions)) == len(self.sources):
            logger.debug("All sources have been looked up")
            self.populateDefinitions()

    def populateDefinitions(self):
        """
        Sort and filter the definitions we found.
        Definitions may be out of order due to concurrency
        """
        index_map = {source.name: i for i, source in enumerate(self.sources)}
        # Sort definitions by source order, stable sort
        self.definitions.sort(key=lambda defi: index_map[defi.source])
        # filter out error definitions
        self.definitions = [defi for defi in self.definitions if defi.definition is not None]
        if not any(defi.definition for defi in self.definitions):
            if self.word_widget:
                self.word_widget.setText(self.current_target)
            self.setPlaceholderText("No definitions found for \"" + self.current_target
                                    + "\". You can still type in a definition manually to add to Anki.")
        else:
            self.setPlaceholderText(DEFAULT_PLACEHOLDER_TEXT)
        self.currentIndex = 0
        self.updateIndex()

    def getFirstDefinition(self, target) -> Optional[Definition]:
        """
        Blocking function to get the first definition from all sources
        For use outside of the main interface
        """
        for source in self.sources:
            logger.debug("Getting definition from source " + source.name)
            for defi in source.define(target):
                logger.debug("Got definition from source " + defi.source + ": " + str(defi))
                if defi.definition is not None:
                    return defi
        return None

    def updateIndex(self):
        if not self.definitions:
            return
        self.counter.setText(f"{self.currentIndex+1}/{len(self.definitions)}")
        if defi := self.definitions[self.currentIndex]:
            self.setCurrentDefinition(defi)

    def setCurrentDefinition(self, defi: Definition):
        self.currentDefinition = defi
        source_name = defi.source
        source = self.getSource(source_name)
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
        self.nextDefinitionScrollTransitionCounter = 0
        if self.currentIndex > 0:
            self.setCurrentIndex(self.currentIndex - 1)
        else:  # wrap around
            self.setCurrentIndex(len(self.definitions) - 1)

    def forward(self):
        self.nextDefinitionScrollTransitionCounter = 0
        if self.currentIndex < len(self.definitions) - 1:
            self.setCurrentIndex(self.currentIndex + 1)
        else:  # wrap around
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
        # TODO try to remove references to threads and workers without crashing # pylint: disable=fixme

    def getSource(self, source_name: str) -> Optional[DictionarySource]:
        for source in self.sources:
            if source.name == source_name:
                return source
        return None

    def toAnki(self, defi: Optional[Definition] = None) -> str:
        """Process definitions before sending to Anki"""
        # Figure out display mode of current source
        maybe_user_typed_text = self.toPlainText().replace("\n", "<br>")
        if defi is not None:  # for non-interactive use
            self.setCurrentDefinition(defi)
        if self.currentDefinition is None:  # This means no definition is found but maybe the user typed in something
            return maybe_user_typed_text
        source_name = self.currentDefinition.source
        source = self.getSource(source_name)
        if source is None:
            raise ValueError(f"Source {source_name} not found, cannot process definition for Anki")

        return process_defi_anki(self.toPlainText(), self.toMarkdown(), self.currentDefinition, source)
