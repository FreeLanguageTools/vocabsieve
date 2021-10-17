#!/usr/bin/env python3
from ssmtool.main import DictionaryWindow
import sys
from PyQt5.QtWidgets import QApplication
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("ssmtool")
    app.setOrganizationName("FreeLanguageTools")
    w = DictionaryWindow()

    w.show()
    sys.exit(app.exec())
