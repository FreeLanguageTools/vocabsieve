from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import platform
from .tools import *
from .dictionary import *
from .dictmanager import *

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.parent = parent
        self.setWindowTitle("Configure VocabSieve")
        self.initWidgets()
        self.initTabs()
        self.setupWidgets()
        self.setupAutosave()
        self.twodictmode = self.settings.value("dict_source2", "<disabled>") != "<disabled>"

    def initWidgets(self):
        self.bar = QStatusBar()
        self.allow_editing = QCheckBox("Allow directly editing definition fields")
        self.primary = QCheckBox("Use primary selection")
        self.register_config_handler(self.allow_editing, "allow_editing", True)
        self.lemmatization = QCheckBox("Use lemmatization for dictionary lookups")
        self.lemmatization.setToolTip("Lemmatization means to get the original form of words."
            + "\nFor example, 'books' will be converted to 'book' during lookup if this option is set.")
        self.lemfreq = QCheckBox("Lemmatize before looking up frequency")
        self.lemfreq.setToolTip("Lemmatize words before trying to find them in the frequency list."
            + "\nUse this for frequency lists displayed on FLT.org, but do not use it "
            + "\nfor frequency lists from Migaku. ")
        self.target_language = QComboBox()
        self.deck_name = QComboBox()
        self.tags = QLineEdit()
        self.dict_source = QComboBox()
        self.dict_source2 = QComboBox()
        self.freq_source = QComboBox()
        self.gtrans_lang = QComboBox()
        self.note_type = QComboBox()
        self.sentence_field = QComboBox()
        self.word_field = QComboBox()
        self.definition_field = QComboBox()
        self.definition2_field = QComboBox()
        self.pronunciation_field = QComboBox()
        self.audio_dict = QComboBox()
        self.bold_word = QCheckBox("Bold word in sentence on lookup")
        self.note_type_url = QLabel("For a suitable note type, \
            download <a href=\"https://freelanguagetools.org/sample.apkg\">this file</a> \
                and import it to your Anki collection.")
        self.note_type_url.setOpenExternalLinks(True)

        self.web_preset = QComboBox()
        self.custom_url = QLineEdit()
        self.custom_url.setText("https://example.com/@@@@")
        self.custom_url.setEnabled(False)

        self.orientation = QComboBox()
        self.text_scale = QSlider(Qt.Horizontal)

        self.text_scale.setTickPosition(QSlider.TicksBelow)
        self.text_scale.setTickInterval(10)
        self.text_scale.setSingleStep(5)
        self.text_scale.setValue(100)
        self.text_scale.setMinimum(50)
        self.text_scale.setMaximum(250)
        self.text_scale_label = QLabel("1.00x")        
        self.text_scale_box = QWidget()
        self.text_scale_box_layout = QHBoxLayout()
        self.text_scale_box.setLayout(self.text_scale_box_layout)
        self.text_scale_box_layout.addWidget(self.text_scale)
        self.text_scale_box_layout.addWidget(self.text_scale_label)

        self.orientation.addItems(["Vertical", "Horizontal"])
        self.gtrans_api = QLineEdit()
        self.anki_api = QLineEdit()


        self.api_enabled = QCheckBox("Enable SSM local API")
        self.api_host = QLineEdit()
        self.api_port = QSpinBox()
        self.api_port.setMinimum(1024)
        self.api_port.setMaximum(49151)

        self.reader_enabled = QCheckBox("Enable SSM Web Reader")
        self.reader_host = QLineEdit()
        self.reader_port = QSpinBox()
        self.reader_port.setMinimum(1024)
        self.reader_port.setMaximum(49151)

        self.importdict = QPushButton('Manage local dictionaries..')

        
        self.importdict.clicked.connect(self.dictmanager)

    def dictmanager(self):
        importer = DictManager(self)
        importer.exec()
        self.loadDictionaries()
        self.loadFreqSources()
        self.loadAudioDictionaries()
    
    def initTabs(self):
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab1.layout = QFormLayout(self.tab1)
        self.tab2 = QWidget()
        self.tab2.layout = QFormLayout(self.tab2)
        self.tab3 = QWidget()
        self.tab3.layout = QFormLayout(self.tab3)
        self.tab4 = QWidget()
        self.tab4.layout = QFormLayout(self.tab4)

        self.tabs.resize(250, 300)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.bar)

        self.tabs.addTab(self.tab1, "Dictionary")
        self.tabs.addTab(self.tab2, "Anki")
        self.tabs.addTab(self.tab3, "Network")
        self.tabs.addTab(self.tab4, "Interface")

    def setupWidgets(self):
        self.target_language.addItems(langs_supported.values())
        self.web_preset.addItems([
            "English Wiktionary",
            "Monolingual Wiktionary",
            "Reverso Context",
            "Tatoeba",
            "Custom (Enter below)"
            ])
        self.gtrans_lang.addItems(langs_supported.values())
        
        self.tab1.layout.addRow(self.lemmatization)
        self.tab1.layout.addRow(self.lemfreq)
        self.tab1.layout.addRow(self.bold_word)
        self.tab1.layout.addRow(QLabel("Target language"), self.target_language)
        self.tab1.layout.addRow(QLabel("Dictionary source 1"), self.dict_source)
        self.tab1.layout.addRow(QLabel("Dictionary source 2"), self.dict_source2)
        self.tab1.layout.addRow(QLabel("Pronunciation source"), self.audio_dict)
        self.tab1.layout.addRow(QLabel("Frequency list"), self.freq_source)
        self.tab1.layout.addRow(QLabel("Google translate: To"), self.gtrans_lang)
        self.tab1.layout.addRow(QLabel("Web lookup preset"), self.web_preset)
        self.tab1.layout.addRow(QLabel("Custom URL pattern"), self.custom_url)
        self.tab1.layout.addRow(self.importdict)


        self.tab2.layout.addRow(QLabel('AnkiConnect API'), self.anki_api)
        self.tab2.layout.addRow(QLabel("Deck name"), self.deck_name)
        self.tab2.layout.addRow(QLabel('Default tags'), self.tags)
        self.tab2.layout.addRow(QLabel("Note type"), self.note_type)
        self.tab2.layout.addRow(QLabel('Field name for "Sentence"'), self.sentence_field)
        self.tab2.layout.addRow(QLabel('Field name for "Word"'), self.word_field)
        self.tab2.layout.addRow(QLabel('Field name for "Definition"'), self.definition_field)
        self.tab2.layout.addRow(QLabel('Field name for "Definition#2"'), self.definition2_field)
        self.tab2.layout.addRow(QLabel('Field name for "Pronunciation"'), self.pronunciation_field)
        self.tab2.layout.addRow(self.note_type_url)

        self.tab3.layout.addRow(QLabel('<i>Most users should not need to change these settings.</i><br><b>All settings on this tab requires restart to take effect.</b>'))
        self.tab3.layout.addRow(self.api_enabled)
        self.tab3.layout.addRow(QLabel("API host"), self.api_host)
        self.tab3.layout.addRow(QLabel("API port"), self.api_port)
        self.tab3.layout.addRow(self.reader_enabled)
        self.tab3.layout.addRow(QLabel("Web reader host"), self.reader_host)
        self.tab3.layout.addRow(QLabel("Web reader port"), self.reader_port)
        self.tab3.layout.addRow(QLabel("Google Translate API"), self.gtrans_api)

        self.tab4.layout.addRow(QLabel("<b>All settings on this tab requires restart to take effect.</b>"))
        if platform.system() == "Linux":
            # Primary selection is only available on Linux
            self.tab4.layout.addRow(self.primary)
        self.tab4.layout.addRow(self.allow_editing)
        self.tab4.layout.addRow(QLabel("Interface layout"), self.orientation)
        self.tab4.layout.addRow(QLabel("Text scale"), self.text_scale_box)


        self.text_scale.valueChanged.connect(
            lambda _: self.text_scale_label.setText(format(self.text_scale.value()/100, "1.2f") + "x")
            )

        
    def setupAutosave(self):
        if self.settings.value("config_ver") == None:
            # if old config is copied to new location, nuke it
            self.settings.clear()
        self.settings.setValue("config_ver", 1)
        self.register_config_handler(self.anki_api, 'anki_api', 'http://localhost:8765')
        self.register_config_handler(self.target_language, 'target_language', 'en', code_translate=True)

        api = self.anki_api.text()
        try:
            _ = getVersion(api)
            self.loadDecks()
            self.loadFields()
            self.register_config_handler(self.deck_name, 'deck_name', 'Default')
            self.register_config_handler(self.tags, 'tags', 'vocabsieve')
            self.register_config_handler(self.note_type, 'note_type', 'Basic')
            self.register_config_handler(self.sentence_field, 'sentence_field', 'Sentence')
            self.register_config_handler(self.word_field, 'word_field', 'Word')
            self.register_config_handler(self.definition_field, 'definition_field', 'Definition')
            self.register_config_handler(self.definition2_field, 'definition2_field', '<disabled>')
            self.register_config_handler(self.pronunciation_field, 'pronunciation_field', "<disabled>")
        except Exception as e:
            self.errorNoConnection(e)

        self.loadDictionaries()
        self.loadAudioDictionaries()
        self.loadFreqSources()

        self.dict_source2.currentTextChanged.connect(self.changeMainLayout)
        self.note_type.currentTextChanged.connect(self.loadFields)
        self.api_enabled.clicked.connect(self.setAvailable)
        self.reader_enabled.clicked.connect(self.setAvailable)
        self.register_config_handler(self.lemmatization, 'lemmatization', True)
        self.register_config_handler(self.lemfreq, 'lemfreq', True)
        self.register_config_handler(self.bold_word, 'bold_word', True)

        self.register_config_handler(self.gtrans_lang, 'gtrans_lang', 'en', code_translate=True)
        self.register_config_handler(self.dict_source, 'dict_source', 'Wiktionary (English)')
        self.register_config_handler(self.dict_source2, 'dict_source2', '<disabled>')
        self.register_config_handler(self.audio_dict, 'audio_dict', 'Forvo')
        self.register_config_handler(self.freq_source, 'freq_source', '<disabled>')
        self.register_config_handler(self.web_preset, 'web_preset', 'English Wiktionary')
        self.register_config_handler(self.custom_url, 'custom_url', "")

     
        self.register_config_handler(self.api_enabled, 'api_enabled', True)
        self.register_config_handler(self.api_host, 'api_host', '127.0.0.1')
        self.register_config_handler(self.api_port, 'api_port', 39284)
        self.register_config_handler(self.reader_enabled, 'reader_enabled', True)
        self.register_config_handler(self.reader_host, 'reader_host', '127.0.0.1')
        self.register_config_handler(self.reader_port, 'reader_port', 39285)
        self.register_config_handler(self.gtrans_api, 'gtrans_api', 'https://lingva.ml')

        self.register_config_handler(self.allow_editing, 'allow_editing', True)
        self.register_config_handler(self.primary, 'primary', False)
        self.register_config_handler(self.orientation, 'orientation', 'Vertical')
        self.register_config_handler(self.text_scale, 'text_scale', '100')

        self.target_language.currentTextChanged.connect(self.loadDictionaries)
        self.target_language.currentTextChanged.connect(self.loadAudioDictionaries)
        self.target_language.currentTextChanged.connect(self.loadFreqSources)
        self.target_language.currentTextChanged.connect(self.loadUrl)
        self.web_preset.currentTextChanged.connect(self.loadUrl)
        self.gtrans_lang.currentTextChanged.connect(self.loadUrl)
    def setAvailable(self):
        self.api_host.setEnabled(self.api_enabled.isChecked())
        self.api_port.setEnabled(self.api_enabled.isChecked())
        self.reader_host.setEnabled(self.reader_enabled.isChecked())
        self.reader_port.setEnabled(self.reader_enabled.isChecked())

    def loadAudioDictionaries(self):
        custom_dicts = json.loads(self.settings.value("custom_dicts", '[]'))
        self.audio_dict.blockSignals(True)
        self.audio_dict.clear()
        dicts = getAudioDictsForLang(langcodes.inverse[self.target_language.currentText()], custom_dicts)
        self.audio_dict.addItems(dicts)
        self.audio_dict.setCurrentText(self.settings.value('audio_dict', "Forvo (all)"))
        self.audio_dict.blockSignals(False)

    def loadDictionaries(self):
        custom_dicts = json.loads(self.settings.value("custom_dicts", '[]'))
        self.dict_source.blockSignals(True)
        self.dict_source.clear()
        self.dict_source2.blockSignals(True)
        self.dict_source2.clear()
        self.dict_source2.addItem("<disabled>")
        dicts = getDictsForLang(langcodes.inverse[self.target_language.currentText()], custom_dicts)
    
        self.dict_source.addItems(dicts)
        self.dict_source2.addItems(dicts)
        self.dict_source.setCurrentText(self.settings.value('dict_source', 'Wiktionary (English)'))
        self.dict_source2.setCurrentText(self.settings.value('dict_source2', '<disabled>'))
        self.dict_source.blockSignals(False)
        self.dict_source2.blockSignals(False)

    def loadFreqSources(self):
        custom_dicts = json.loads(self.settings.value("custom_dicts", '[]'))
        sources = getFreqlistsForLang(langcodes.inverse[self.target_language.currentText()], custom_dicts)
        self.freq_source.blockSignals(True)
        self.freq_source.clear()
        self.freq_source.addItem("<disabled>")
        for item in sources:
            self.freq_source.addItem(item)
        self.freq_source.setCurrentText(self.settings.value("freq_source", "<disabled>"))
        self.freq_source.blockSignals(False)

    def loadUrl(self):
        lang = self.settings.value("target_language", "en")
        tolang = self.settings.value("gtrans_lang", "en")
        langfull = langcodes[lang]
        tolangfull = langcodes[tolang]
        self.presets = bidict({
            "English Wiktionary": "https://en.wiktionary.org/wiki/@@@@#" + langfull, 
            "Monolingual Wiktionary": f"https://{lang}.wiktionary.org/wiki/@@@@",
            "Reverso Context": f"https://context.reverso.net/translation/{langfull.lower()}-{tolangfull.lower()}/@@@@",
            "Tatoeba": "https://tatoeba.org/en/sentences/search?query=@@@@"
            })

        if self.web_preset.currentText() == "Custom (Enter below)":
            self.custom_url.setEnabled(True)
            self.custom_url.setText(self.settings.value("custom_url"))
        else:
            self.custom_url.setEnabled(False)
            self.custom_url.setText(self.presets[self.web_preset.currentText()])

    def loadDecks(self):
        self.status("Loading decks")
        api = self.anki_api.text()
        decks = getDeckList(api)
        self.deck_name.blockSignals(True)
        self.deck_name.clear()
        self.deck_name.addItems(decks)
        self.deck_name.setCurrentText(self.settings.value("deck_name"))
        self.deck_name.blockSignals(False)

        note_types = getNoteTypes(api)
        self.note_type.blockSignals(True)
        self.note_type.clear()
        self.note_type.addItems(note_types)
        self.note_type.setCurrentText(self.settings.value("note_type"))
        self.note_type.blockSignals(False)

    def loadFields(self):
        self.status("Loading fields")
        api = self.anki_api.text()
    
        current_type = self.note_type.currentText()
        if current_type == "":
            return

        fields = getFields(api, current_type)
        # Temporary store fields 
        sent = self.sentence_field.currentText()
        word = self.word_field.currentText()
        def1 = self.definition_field.currentText()
        def2 = self.definition2_field.currentText()
        pron = self.pronunciation_field.currentText()

        # Block signals temporarily to avoid warning dialogs
        self.sentence_field.blockSignals(True)
        self.word_field.blockSignals(True)
        self.definition_field.blockSignals(True)
        self.definition2_field.blockSignals(True)
        self.pronunciation_field.blockSignals(True)

        self.sentence_field.clear()
        self.sentence_field.addItems(fields)

        self.word_field.clear()
        self.word_field.addItems(fields)

        self.definition_field.clear()
        self.definition_field.addItems(fields)

        self.definition2_field.clear()
        self.definition2_field.addItem("<disabled>")
        self.definition2_field.addItems(fields)     

        self.pronunciation_field.clear()
        self.pronunciation_field.addItem("<disabled>")
        self.pronunciation_field.addItems(fields)   

        self.sentence_field.setCurrentText(self.settings.value("sentence_field"))
        self.word_field.setCurrentText(self.settings.value("word_field"))
        self.definition_field.setCurrentText(self.settings.value("definition_field"))
        self.definition2_field.setCurrentText(self.settings.value("definition2_field"))
        self.pronunciation_field.setCurrentText(self.settings.value("pronunciation_field"))

        if self.sentence_field.findText(sent) != -1:
            self.sentence_field.setCurrentText(sent)
        if self.word_field.findText(word) != -1:
            self.word_field.setCurrentText(word)
        if self.definition_field.findText(def1) != -1:
            self.definition_field.setCurrentText(def1)
        if self.definition2_field.findText(def2) != -1:
            self.definition2_field.setCurrentText(def2)
        if self.pronunciation_field.findText(pron) != -1:
            self.pronunciation_field.setCurrentText(pron)
        
        self.sentence_field.blockSignals(False)
        self.word_field.blockSignals(False)
        self.definition_field.blockSignals(False)
        self.definition2_field.blockSignals(False)
        self.pronunciation_field.blockSignals(False)
        self.status("Done")
    
    def errorNoConnection(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(str(error) + 
            "\nAnkiConnect must be running to set Anki-related options."
            "\nIf you have AnkiConnect set up at a different endpoint, set that now "
            "and reopen the config tool")
        msg.exec()


    def changeMainLayout(self):
        if self.dict_source2.currentText() != "<disabled>":
            # This means user has changed from one source to two source mode, 
            # need to redraw main window
            if self.settings.value("orientation", "Vertical") == "Vertical":
                self.parent.layout.removeWidget(self.parent.definition)
                self.parent.layout.addWidget(self.parent.definition, 7, 0, 2, 3)
                self.parent.layout.addWidget(self.parent.definition2, 9, 0, 2, 3)
                self.parent.definition2.setVisible(True)
            else:
                self.parent.layout.removeWidget(self.parent.definition)
                self.parent.layout.addWidget(self.parent.definition, 2, 3, 2, 2)
                self.parent.layout.addWidget(self.parent.definition2, 4, 3, 2, 2)
                self.parent.definition2.setVisible(True)
        else:
            self.parent.layout.removeWidget(self.parent.definition)
            self.parent.layout.removeWidget(self.parent.definition2)
            self.parent.definition2.setVisible(False)
            if self.settings.value("orientation", "Vertical") == "Vertical":
                self.parent.layout.addWidget(self.parent.definition, 7, 0, 4, 3)
            else:
                self.parent.layout.addWidget(self.parent.definition, 2, 3, 4, 2)

    def status(self, msg):
        self.bar.showMessage(self.parent.time() + " " + msg, 4000)

    def register_config_handler(self, widget, key, default, code_translate=False):
        name = widget.objectName()
        update = lambda v: self.settings.setValue(key, v)
        update_map = lambda v: self.settings.setValue(key, langcodes.inverse[v])
        if type(widget) == QCheckBox:
            widget.setChecked(self.settings.value(key, default, type=bool))
            widget.clicked.connect(update)
            update(widget.isChecked())
        if type(widget) == QLineEdit:
            widget.setText(self.settings.value(key, default))
            widget.textChanged.connect(update)
            update(widget.text())
        if type(widget) == QComboBox:
            if code_translate:
                widget.setCurrentText(langcodes[self.settings.value(key, default)])
                widget.currentTextChanged.connect(update_map)
                update_map(widget.currentText())
            else:
                widget.setCurrentText(self.settings.value(key, default))
                widget.currentTextChanged.connect(update)
                update(widget.currentText())
        if type(widget) == QSlider or type(widget) == QSpinBox:
            widget.setValue(self.settings.value(key, default, type=int))
            widget.valueChanged.connect(update)
            update(widget.value())