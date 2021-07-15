from PyQt5.QtWidgets import *
from .tools import *

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
        self.resize(320, 350)
        self.allow_editing = QCheckBox("Allow directly editing (Requires restart to take effect)")
        self.lemmatization = QCheckBox("Use lemmatization (Experimental)")
        self.target_language = QComboBox()
        self.deck_name = QComboBox()
        self.tags = QLineEdit()
        self.note_type = QComboBox()
        self.sentence_field = QComboBox()
        self.word_field = QComboBox()
        self.definition_field = QComboBox()
        self.anki_api = QLineEdit()

    def setupWidgets(self):
        languages = code.keys()
        self.target_language.addItems(languages)
        self.layout.addWidget(self.allow_editing, 0, 0, 1, 2)
        self.layout.addWidget(self.lemmatization, 1, 0, 1, 2)

        self.layout.addWidget(QLabel("Target language"), 2, 0)
        self.layout.addWidget(self.target_language, 2, 1)

        self.layout.addWidget(QLabel('AnkiConnect API'), 3, 0)
        self.layout.addWidget(self.anki_api, 3,1)

        self.layout.addWidget(QLabel("Deck name"), 4, 0)
        self.layout.addWidget(self.deck_name, 4, 1)

        self.layout.addWidget(QLabel('Default tags'), 5, 0)
        self.layout.addWidget(self.tags, 5, 1)

        self.layout.addWidget(QLabel("Note type"), 6, 0)
        self.layout.addWidget(self.note_type, 6,1)

        self.layout.addWidget(QLabel('Field name for "Sentence"'), 7, 0)
        self.layout.addWidget(self.sentence_field, 7, 1)

        self.layout.addWidget(QLabel('Field name for "Word"'), 8, 0)
        self.layout.addWidget(self.word_field, 8, 1)

        self.layout.addWidget(QLabel('Field name for "Definition"'), 9, 0)
        self.layout.addWidget(self.definition_field, 9, 1)


        
    def setupAutosave(self):
        self.allow_editing.clicked.connect(self.syncSettings)
        self.lemmatization.clicked.connect(self.syncSettings)
        self.target_language.currentTextChanged.connect(self.syncSettings)
        self.deck_name.currentTextChanged.connect(self.syncSettings)
        self.tags.editingFinished.connect(self.syncSettings)
        self.note_type.currentTextChanged.connect(self.syncSettings)
        self.note_type.currentTextChanged.connect(self.loadFields)
        self.sentence_field.currentTextChanged.connect(self.syncSettings)
        self.word_field.currentTextChanged.connect(self.syncSettings)
        self.definition_field.currentTextChanged.connect(self.syncSettings)
        self.anki_api.editingFinished.connect(self.syncSettings)
        self.anki_api.editingFinished.connect(self.loadSettings)

    def loadSettings(self):
        print("loading, will also check api")
        self.allow_editing.setChecked(self.settings.value("allow_editing", True, type=bool))
        self.lemmatization.setChecked(self.settings.value("lemmatization", True, type=bool))
        self.target_language.setCurrentText(self.settings.value("target_language"))
        self.anki_api.setText(self.settings.value("anki_api", "http://localhost:8765"))
        self.tags.setText(self.settings.value("tags", "ssmtool"))

        api = self.anki_api.text()

        try:
            print("API version is: ", getVersion(api))
        except Exception as e:
            self.errorNoConnection(e)
            return

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
        try:
            print("API version is: ", getVersion(api))
        except Exception as e:
            self.errorNoConnection(e)
            return
        current_type = self.note_type.currentText()
        print("Current note type is:", current_type) 

        if current_type == "":
            return

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
        self.settings.setValue("tags", self.tags.text())
        self.settings.setValue("note_type", self.note_type.currentText())
        self.settings.setValue("sentence_field", self.sentence_field.currentText())
        self.settings.setValue("word_field", self.word_field.currentText())
        self.settings.setValue("definition_field", self.definition_field.currentText())
        self.settings.setValue("anki_api", self.anki_api.text())
        self.settings.sync()
    
    def errorNoConnection(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(str(error) + 
            "\nAnkiConnect must be running to use the configuration tool.")
        msg.exec()