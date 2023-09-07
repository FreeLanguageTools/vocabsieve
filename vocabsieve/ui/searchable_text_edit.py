from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ..global_events import GlobalObject
from ..app_text import settings_app_title, app_organization

settings = QSettings(app_organization, settings_app_title)

class SearchableTextEdit(QTextEdit):

    @pyqtSlot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        if not settings.value("lookup_definition_on_doubleclick", True, type=bool):
            return
        GlobalObject().dispatchEvent("double clicked")
        self.textCursor().clearSelection()
        self.original = ""