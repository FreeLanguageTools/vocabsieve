from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QWidget, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QT_VERSION_STR, PYQT_VERSION_STR
import sys

from ..global_names import session_logs
from .. import __version__



class LogView(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Session logs")
        self.resize(800, 600)

        btn_copy = QPushButton("Copy to clipboard")
        btn_dismiss = QPushButton("Dismiss")
        btn_dismiss.clicked.connect(self.accept)

        button_box = QWidget()
        button_box_layout = QHBoxLayout(button_box)
        button_box_layout.addWidget(btn_copy)
        button_box_layout.addWidget(btn_dismiss)
        self._layout = QVBoxLayout()
        message = f'''VocabSieve version: {__version__}
Python version: {sys.version}
PyQt5 (Qt bindings) version: {QT_VERSION_STR}, Qt {PYQT_VERSION_STR}\n\n'''
        message_label = QLabel(message)
        message_label.setTextFormat(Qt.PlainText)
        message_label.setOpenExternalLinks(True)
        message_label.setWordWrap(True)
        message_label.adjustSize()

        log_textedit = QTextEdit()
        log_textedit.setReadOnly(True)
        log_textedit.setPlainText(message + session_logs.getvalue())
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(
                message + session_logs.getvalue()
            )
        )
        self._layout.addWidget(message_label)
        self._layout.addWidget(log_textedit)
        self._layout.addWidget(button_box)
        self.setLayout(self._layout)