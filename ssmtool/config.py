from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from .tools import *
from .dictionary import *

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.parent = parent
        self.initWidgets()
        self.initTabs()
        self.setupWidgets()
        self.loadSettings()
        self.setupAutosave()

    def initWidgets(self):
        self.allow_editing = QCheckBox("Allow directly editing of text fields (Requires restart to take effect)")
        self.lemmatization = QCheckBox("Use lemmatization (Requires restart to take effect)")
        self.lemmatization.setToolTip("Lemmatization means to get the original form of words."
            + "\nFor example, 'books' will be converted to 'book' during lookup if this option is set.")
        self.target_language = QComboBox()
        self.deck_name = QComboBox()
        self.tags = QLineEdit()
        self.dict_source = QComboBox()
        self.note_type = QComboBox()
        self.sentence_field = QComboBox()
        self.word_field = QComboBox()
        self.definition_field = QComboBox()
        self.anki_api = QLineEdit()
        self.about_sa = QScrollArea()
        #self.about_sa.setAlignment()
        self.about = QLabel(
            '''
© 2021 FreeLanguageTools<br><br>
Simple Sentence Mining (ssmtool) is free software available under the terms of \
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.<br><br>
If you found a bug, or have enhancement ideas, \
feel free to open an issue on the \
Github <a href=https://github.com/FreeLanguageTools/ssmtool>repository</a>.
<br><br>
This program is yours to keep. There is no EULA you need to agree to. \
No data is sent to any server other than the configured dictionary APIs. \
Statistics data are stored locally.
<br><br>
Credits: <br><a href="https://en.wiktionary.org/wiki/Wiktionary:Main_Page">Wiktionary API</a><br>
<a href="https://dictionaryapi.dev/">Google Dictionary API</a><br>
If you find this tool useful, you probably should donate to these projects.
            '''
        )
        self.about.setTextFormat(Qt.RichText)
        self.about.setOpenExternalLinks(True)
        self.about_sa.setWidget(self.about)
        self.about.setWordWrap(True)
        self.about.adjustSize()

    
    def initTabs(self):
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab1.layout = QFormLayout(self.tab1)
        self.tab2 = QWidget()
        self.tab2.layout = QFormLayout(self.tab2)
        self.tab3 = QWidget()
        self.tab3.layout = QFormLayout(self.tab3)
        self.tab4 = QWidget()
        self.tab4.layout = QVBoxLayout(self.tab4)

        self.tabs.resize(250, 300)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)

        self.tabs.addTab(self.tab1, "Dictionary")
        self.tabs.addTab(self.tab2, "Anki")
        self.tabs.addTab(self.tab3, "Miscellaneous")
        self.tabs.addTab(self.tab4, "About")

    def setupWidgets(self):
        self.target_language.addItems(code.keys())
        
        self.tab1.layout.addRow(self.lemmatization)
        self.tab1.layout.addRow(QLabel("Target language"), self.target_language)
        self.tab1.layout.addRow(QLabel("Dictionary source"), self.dict_source)
        self.tab2.layout.addRow(QLabel('AnkiConnect API'), self.anki_api)
        self.tab2.layout.addRow(QLabel("Deck name"), self.deck_name)
        self.tab2.layout.addRow(QLabel('Default tags'), self.tags)
        self.tab2.layout.addRow(QLabel("Note type"), self.note_type)
        self.tab2.layout.addRow(QLabel('Field name for "Sentence"'), self.sentence_field)
        self.tab2.layout.addRow(QLabel('Field name for "Word"'), self.word_field)
        self.tab2.layout.addRow(QLabel('Field name for "Definition"'), self.definition_field)

        self.tab3.layout.addRow(self.allow_editing)

        self.tab4.layout.addWidget(self.about_sa)
        


        
    def setupAutosave(self):
        self.allow_editing.clicked.connect(self.syncSettings)
        self.lemmatization.clicked.connect(self.syncSettings)
        self.dict_source.currentTextChanged.connect(self.syncSettings)
        self.target_language.currentTextChanged.connect(self.loadDictionaries)
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

    def loadDictionaries(self):
        self.dict_source.clear()
        self.dict_source.addItem("Wiktionary (English)")
        self.dict_source.addItem("Google translate (To English)")
        if code[self.target_language.currentText()] in gdict_languages:
            self.dict_source.addItem("Google dictionary (Monolingual)")


    def loadSettings(self):
        self.allow_editing.setChecked(self.settings.value("allow_editing", True, type=bool))
        self.lemmatization.setChecked(self.settings.value("lemmatization", True, type=bool))
        self.target_language.setCurrentText(self.settings.value("target_language"))
        self.loadDictionaries()
        self.dict_source.setCurrentText(self.settings.value("dict_source", "Wiktionary (English)"))
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
        self.settings.setValue("dict_source", self.dict_source.currentText())
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