from PyQt5.QtGui import QMouseEvent, QTextCursor
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import QEvent, Qt, QObject, pyqtSlot
from ..global_events import GlobalObject
from ..global_names import settings

class SearchableTextEdit(QTextEdit):
    def __init__(self):
        super(SearchableTextEdit, self).__init__()
        self.setMouseTracking(True)
        self.word_under_cursor = ""

    @pyqtSlot()
    def mouseDoubleClickEvent(self, e) -> None:
        super().mouseDoubleClickEvent(e)
        if not settings.value("lookup_definition_on_doubleclick", True, type=bool):
            return
        GlobalObject().dispatchEvent("double clicked")
        self.textCursor().clearSelection()
        self.original: str = ""

    @pyqtSlot()
    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        super().mouseMoveEvent(e)
        if not settings.value("lookup_definition_when_hovering", True, type=bool):
            return
        
        text_cursor: QTextCursor = self.cursorForPosition(e.pos()) 
        text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        self.word_under_cursor = text_cursor.selectedText()
        GlobalObject().dispatchEvent("hovered over")
