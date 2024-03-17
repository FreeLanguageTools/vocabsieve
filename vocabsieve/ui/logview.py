from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QWidget, QPlainTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtGui import QFont
import sys
import platform

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

        warn_message = QLabel("Be careful to check for sensitive information before sharing any logs!")

        self._layout = QVBoxLayout()

        message = f'''VocabSieve version: {__version__}
Python version: {sys.version} on {platform.system()} {platform.release()} {platform.machine()}
PyQt5 (Qt bindings) version: {PYQT_VERSION_STR}, Qt {QT_VERSION_STR}\n\n'''
        message_label = QLabel(message)
        message_label.setTextFormat(Qt.PlainText)
        message_label.setOpenExternalLinks(True)
        message_label.setWordWrap(True)
        message_label.adjustSize()

        log_textedit = QPlainTextEdit()
        font = log_textedit.font()
        font.setFamily("foobar")  # non-existent font to use default mono font
        font.setStyleHint(QFont.Monospace)
        log_textedit.setFont(font)
        log_textedit.setReadOnly(True)
        log_textedit.setPlainText(message + session_logs.getvalue())
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(
            message + session_logs.getvalue()
        )
        )
        self._layout.addWidget(message_label)
        self._layout.addWidget(warn_message)
        self._layout.addWidget(log_textedit)
        self._layout.addWidget(button_box)
        self.setLayout(self._layout)
