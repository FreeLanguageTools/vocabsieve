from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import traceback
from loguru import logger
import sys


class ExceptionCatcher(QObject):
    exception_signal = pyqtSignal(object, object, object)

    def __init__(self):
        super().__init__()
        sys.excepthook = self.except_hook
        self.exception_signal.connect(self.make_error_box)

    def make_error_box(self, e_type, e_value, e_trace):
        logger.error("".join(traceback.format_exception(e_type, e_value, e_trace)))
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(traceback.format_exception_only(e_type, e_value)[-1])
        msg.setInformativeText("".join(traceback.format_exception(e_type, e_value, e_trace)[:10]))
        msg.exec()

    def except_hook(self, e_type, e_value, e_trace):
        # To avoid CTRL+C causing an error
        if e_type != KeyboardInterrupt:
            self.exception_signal.emit(e_type, e_value, e_trace)
