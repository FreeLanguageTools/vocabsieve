from PyQt5.QtWidgets import (QDialog, QStatusBar, QCheckBox, QComboBox, QLineEdit,
                             QSpinBox, QPushButton, QSlider, QLabel, QHBoxLayout,
                             QWidget, QTabWidget, QMessageBox, QColorDialog, QListWidget,
                             QFormLayout, QGridLayout, QVBoxLayout
                             )
from PyQt5.QtGui import QImageWriter
from PyQt5.QtCore import Qt, QTimer
from enum import Enum
import json
from ..constants import langcodes
from ..global_names import settings


class BaseTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout_ = QFormLayout(self)
        self.initWidgets()
        self.setupAutosave()

    def initWidgets(self):
        pass

    def setupAutosave(self):
        pass

    @staticmethod
    def register_config_handler(
            widget,
            key,
            default,
            code_translate=False,
            no_initial_update=False):

        def update(v):
            settings.setValue(key, v)

        def update_map(v):
            settings.setValue(key, langcodes.inverse[v])

        def update_json(v):
            settings.setValue(key, json.dumps(v))

        if isinstance(widget, QCheckBox):
            widget.setChecked(settings.value(key, default, type=bool))
            widget.clicked.connect(update)
            if not no_initial_update:
                update(widget.isChecked())
        if isinstance(widget, QLineEdit):
            widget.setText(settings.value(key, default))
            widget.textChanged.connect(update)
            update(widget.text())
        if isinstance(widget, QComboBox):
            if code_translate:
                widget.setCurrentText(
                    langcodes[settings.value(key, default)])
                widget.currentTextChanged.connect(update_map)
                update_map(widget.currentText())
            elif isinstance(default, Enum):  # if default is an enum type
                widget.setCurrentText(settings.value(key, default.value))
                widget.currentTextChanged.connect(update)
                update(widget.currentText())
            else:
                widget.setCurrentText(settings.value(key, default))
                widget.currentTextChanged.connect(update)
                update(widget.currentText())
        if isinstance(widget, QSlider) or isinstance(widget, QSpinBox):
            widget.setValue(settings.value(key, default, type=int))
            widget.valueChanged.connect(update)
            update(widget.value())
        if isinstance(widget, QListWidget):
            widget.addItems(json.loads(settings.value(key, json.dumps([]), type=str)))
            model = widget.model()
            model.rowsMoved.connect(
                lambda: update_json(
                    [widget.item(i).text() for i in range(widget.count())]  # type: ignore
                )
            )
            # Need to use a QTimer here to delay accessing the model until after the rows have been inserted
            model.rowsInserted.connect(
                lambda: QTimer.singleShot(0,
                                          lambda: update_json(
                                              [widget.item(i).text() for i in range(widget.count())]  # type: ignore
                                          )
                                          )
            )
            model.rowsRemoved.connect(
                lambda: QTimer.singleShot(0,
                                          lambda: update_json(
                                              [widget.item(i).text() for i in range(widget.count())]  # type: ignore
                                          )
                                          )
            )
