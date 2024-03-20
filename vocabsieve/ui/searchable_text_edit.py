from PyQt5.QtGui import QMouseEvent, QTextCursor
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from ..global_names import settings


class SearchableTextEdit(QTextEdit):
    double_clicked = pyqtSignal(str)
    hovered_over = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.word_under_cursor = ""
        self.prev_emitted_word = ""

    @pyqtSlot()
    def mouseDoubleClickEvent(self, e) -> None:
        super().mouseDoubleClickEvent(e)
        if not settings.value("lookup_definition_on_doubleclick", True, type=bool):
            return
        text_cursor: QTextCursor = self.cursorForPosition(e.pos())
        text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = text_cursor.selectedText()
        self.double_clicked.emit(word)
        self.textCursor().clearSelection()

    @pyqtSlot()
    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        super().mouseMoveEvent(e)
        text_cursor: QTextCursor = self.cursorForPosition(e.pos())
        text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = text_cursor.selectedText()
        self.word_under_cursor = word  # always store
        if not settings.value("lookup_definition_when_hovering", True, type=bool):
            return
        # but only emit if it's different from the last one and not empty
        if word != self.prev_emitted_word and word:
            self.hovered_over.emit(word)
            self.prev_emitted_word = word
