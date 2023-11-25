from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QT_VERSION_STR, PYQT_VERSION_STR
import sys

from ..global_names import session_logs
from .. import __version__



class LogView(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Session logs")
        self.resize(800, 600)

        btn_ok = QDialogButtonBox.Ok
        btn_cp = QPushButton("Copy to clipboard")

        self.buttonBox = QDialogButtonBox(btn_ok)
        self.buttonBox.accepted.connect(self.accept)

        self._layout = QVBoxLayout()
        message = QLabel(
            f'''
VocabSieve version: {__version__}<br>
Python version: {sys.version}<br>
PyQt5 (Qt bindings) version: {QT_VERSION_STR}, Qt {PYQT_VERSION_STR}<br><br>
            '''
        )
        message.setTextFormat(Qt.RichText)
        message.setOpenExternalLinks(True)
        message.setWordWrap(True)
        message.adjustSize()

        log_textedit = QTextEdit()
        log_textedit.setReadOnly(True)
        log_textedit.setPlainText(session_logs.getvalue())
        self._layout.addWidget(message)
        self._layout.addWidget(log_textedit)
        self._layout.addWidget(self.buttonBox)
        self.setLayout(self._layout)