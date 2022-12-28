from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from ..global_events import GlobalObject

class SearchableTextEdit(QTextEdit):

    @Slot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        GlobalObject().dispatchEvent("double clicked")
        self.textCursor().clearSelection()
        self.original = ""