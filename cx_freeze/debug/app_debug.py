#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VocabSieve")
    app.setOrganizationName("FreeLanguageTools")
    from vocabsieve.main import DictionaryWindow
    w = DictionaryWindow()
    w.show()
    sys.exit(app.exec())
