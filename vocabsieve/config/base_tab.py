from PyQt5.QtWidgets import (QCheckBox, QComboBox, QLineEdit, QSpinBox, QSlider, QWidget, QListWidget)
from PyQt5.QtCore import QTimer
from enum import Enum
import json
from ..constants import langcodes
from ..global_names import settings


class BaseTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initWidgets()
        self.setupWidgets()
        self.setupLayout()
        self.setupAutosave()

    def initWidgets(self):
        """
        This method should create the necessary widgets
        """

    def setupWidgets(self):
        """
        This method should set up widgets, such as populating fields
        with possible values and connecting signals other than autosaving
        """

    def setupLayout(self):
        """
        This method should set up the layout of the tab
        """

    def setupAutosave(self):
        """
        This method should connect widgets to the settings using register_config_handler
        """

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
