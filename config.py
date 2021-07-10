from PyQt6.QtWidgets import QDialog, QCheckBox, QGridLayout, QLineEdit, QComboBox, QLabel
from tools import getDeckList, getNoteTypes, getFields

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.initWidgets()
        self.setupWidgets()
        self.loadSettings()
        self.setupAutosave()

    def initWidgets(self):
        self.layout = QGridLayout(self)

        self.allow_editing = QCheckBox("Allow directly editing")
        self.lemmatization = QCheckBox("Use lemmatization (NOT IMPLEMENTED)")
        self.target_language = QComboBox()
        self.deck_name = QComboBox()
        self.note_type = QComboBox()
        self.sentence_field = QComboBox()
        self.word_field = QComboBox()
        self.definition_field = QComboBox()
        self.anki_api = QLineEdit()

    def setupWidgets(self):
        languages = [
            "english",
            "french",
            "spanish",
            "russian",
            "japanese",
            "italian",
            "chinese"
        ]
        self.target_language.addItems(languages)
        self.layout.addWidget(self.allow_editing, 0, 0, 1, 2)
        self.layout.addWidget(self.lemmatization, 1, 0, 1, 2)
        self.lemmatization.setCheckable(False)

        self.layout.addWidget(QLabel("Target language"), 2, 0)
        self.layout.addWidget(self.target_language, 2, 1)

        self.layout.addWidget(QLabel('API endpoint for AnkiConnect'), 3, 0)
        self.layout.addWidget(self.anki_api, 3,1)

        self.layout.addWidget(QLabel("Deck name"), 4, 0)
        self.layout.addWidget(self.deck_name, 4, 1)

        self.layout.addWidget(QLabel("Note type"), 5, 0)
        self.layout.addWidget(self.note_type, 5,1)

        self.layout.addWidget(QLabel('Field name for "Sentence"'), 6, 0)
        self.layout.addWidget(self.sentence_field, 6, 1)

        self.layout.addWidget(QLabel('Field name for "Word"'), 7, 0)
        self.layout.addWidget(self.word_field, 7, 1)

        self.layout.addWidget(QLabel('Field name for "Definition"'), 8, 0)
        self.layout.addWidget(self.definition_field, 8, 1)


        
    def setupAutosave(self):
        self.allow_editing.clicked.connect(self.syncSettings)
        self.lemmatization.clicked.connect(self.syncSettings)
        self.target_language.currentTextChanged.connect(self.syncSettings)
        self.deck_name.currentTextChanged.connect(self.syncSettings)
        self.note_type.currentTextChanged.connect(self.syncSettings)
        self.note_type.currentTextChanged.connect(self.loadFields)
        self.sentence_field.currentTextChanged.connect(self.syncSettings)
        self.word_field.currentTextChanged.connect(self.syncSettings)
        self.definition_field.currentTextChanged.connect(self.syncSettings)
        self.anki_api.editingFinished.connect(self.syncSettings)

    def loadSettings(self):
        print("loading")
        self.allow_editing.setChecked(self.settings.value("allow_editing", True, type=bool))
        self.lemmatization.setChecked(self.settings.value("lemmatization", type=bool))
        self.target_language.setCurrentText(self.settings.value("target_language"))
        self.anki_api.setText(self.settings.value("anki_api", "http://localhost:8765"))

        api = self.anki_api.text()

        decks = getDeckList(api)
        self.deck_name.clear()
        self.deck_name.addItems(decks)
        self.deck_name.setCurrentText(self.settings.value("deck_name"))

        note_types = getNoteTypes(api)
        self.note_type.clear()
        self.note_type.addItems(note_types)
        self.note_type.setCurrentText(self.settings.value("note_type"))
        self.loadFields()

    def loadFields(self):
        print("loading fields")
        api = self.anki_api.text()
        current_type = self.note_type.currentText()
        fields = getFields(api, current_type)

        self.sentence_field.clear()
        self.sentence_field.addItems(fields)
        self.word_field.clear()
        self.word_field.addItems(fields)
        self.definition_field.clear()
        self.definition_field.addItems(fields)
        
        self.sentence_field.setCurrentText(self.settings.value("sentence_field"))
        self.word_field.setCurrentText(self.settings.value("word_field"))
        self.definition_field.setCurrentText(self.settings.value("definition_field"))


    def syncSettings(self):
        print("syncing")
        self.settings.setValue("allow_editing", self.allow_editing.isChecked())
        self.settings.setValue("lemmatization", self.lemmatization.isChecked())
        self.settings.setValue("target_language", self.target_language.currentText())
        self.settings.setValue("deck_name", self.deck_name.currentText())
        self.settings.setValue("note_type", self.note_type.currentText())
        self.settings.setValue("sentence_field", self.sentence_field.currentText())
        self.settings.setValue("word_field", self.word_field.currentText())
        self.settings.setValue("definition_field", self.definition_field.currentText())
        self.settings.setValue("anki_api", self.anki_api.text())
        self.settings.sync()