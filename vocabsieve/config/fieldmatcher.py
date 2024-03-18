from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox
import json
from ..tools import getNoteTypes, getFields
from ..global_names import settings


class FieldMatcher(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        api = settings.value("anki_api", "http://127.0.0.1:8765")
        self.models = getNoteTypes(api)
        if not self.models:
            return
        self.fields = {}
        for model in self.models:
            self.fields[model] = getFields(api, model)
        self._layout = QGridLayout(self)

        self.word_comboboxes = {}
        self.ctx_comboboxes = {}
        self._layout.addWidget(
            QLabel(
                "Select fields for each note type to be used either as context or target word.<br>"
                "Everything is saved automatically."),
            0,
            0,
            1,
            3)
        self._layout.addWidget(QLabel("<b>Note type</b>"), 1, 0)
        self._layout.addWidget(QLabel("<b>Word field</b>"), 1, 1)
        self._layout.addWidget(QLabel("<b>Context field</b>"), 1, 2)
        for i, model in enumerate(self.models):
            row = i + 2
            self._layout.addWidget(QLabel(model), row, 0)
            self.word_comboboxes[model] = QComboBox()
            self.word_comboboxes[model].addItem("<Ignore>")
            self.word_comboboxes[model].addItems(self.fields[model])
            self._layout.addWidget(self.word_comboboxes[model], row, 1)
            self.ctx_comboboxes[model] = QComboBox()
            self.ctx_comboboxes[model].addItem("<Ignore>")
            self.ctx_comboboxes[model].addItems(self.fields[model])
            self._layout.addWidget(self.ctx_comboboxes[model], row, 2)
        self.loadSettings()
        self.saveSettings()
        for combobox in self.word_comboboxes.values():
            combobox.currentTextChanged.connect(self.saveSettings)
        for combobox in self.ctx_comboboxes.values():
            combobox.currentTextChanged.connect(self.saveSettings)

    def try_candidates(self, combobox, candidates):
        fields = [combobox.itemText(i) for i in range(combobox.count())]
        for item in candidates:
            if item in fields:
                combobox.setCurrentText(item)
                return

    def loadSettings(self):
        data = json.loads(settings.value("tracking/fieldmap", "{}"))
        for model in self.models:
            word_field, ctx_field = data.get(model) or [None, None]
            if word_field:
                self.word_comboboxes[model].setCurrentText(word_field)
            else:
                self.try_candidates(self.word_comboboxes[model],
                                    ["Word", "Term"]
                                    )
            if ctx_field:
                self.ctx_comboboxes[model].setCurrentText(ctx_field)
            else:
                self.try_candidates(self.ctx_comboboxes[model],
                                    ["Sentence", "Context", "Example"]
                                    )

    def saveSettings(self):
        data = {}
        for model in self.models:
            word_field = self.word_comboboxes[model].currentText()
            ctx_field = self.ctx_comboboxes[model].currentText()
            data[model] = [word_field, ctx_field]
        settings.setValue("tracking/fieldmap", json.dumps(data))
