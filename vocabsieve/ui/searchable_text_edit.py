from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSlot
from ..global_events import GlobalObject
from ..global_names import settings

class SearchableTextEdit(QTextEdit):

    @pyqtSlot()
    def mouseDoubleClickEvent(self, e) -> None:
        super().mouseDoubleClickEvent(e)
        if not settings.value("lookup_definition_on_doubleclick", True, type=bool):
            return
        GlobalObject().dispatchEvent("double clicked")
        self.textCursor().clearSelection()
        self.original: str = ""