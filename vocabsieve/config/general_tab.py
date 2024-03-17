import json
from bidict import bidict
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox
from .base_tab import BaseTab
from ..constants import langcodes
from ..dictmanager import DictManager
from ..dictionary import getFreqlistsForLang, getDictsForLang, getAudioDictsForLang, langs_supported
from ..global_names import settings

BoldStyles = ["<disabled>", "Font weight", "Underscores"]

class GeneralTab(BaseTab):
    def __init__(self):
        self.target_language = QComboBox()
        self.lemfreq = QCheckBox("Lemmatize before looking up frequency")
        self.lemfreq.setToolTip(
            "Lemmatize words before trying to find them in the frequency list." +
            "\nUse this for frequency lists displayed on FLT.org, but do not use it " +
            "\nfor frequency lists from Migaku. ")
        self.bold_style = QComboBox()
        self.bold_style.setToolTip(
            '"Font weight" bolds words directly on the textbox.\n'
            '"Underscores" displays bolded words in double underscores, __word__\n'
            '(Both will look the same in Anki)\n'
            '"<disabled>" disables bolding words in both Vocabsieve and Anki')
        self.audio_format = QComboBox()
        self.audio_format.addItems(
            ['mp3', 'ogg']
        )
        self.freq_source = QComboBox()
        self.gtrans_lang = QComboBox()
        self.web_preset = QComboBox()
        self.custom_url = QLineEdit()
        self.custom_url.setText("https://example.com/@@@@")
        self.custom_url.setEnabled(False)
        self.importdict = QPushButton('Manage local resources..')
        self.importdict.clicked.connect(self.dictmanager)
        self.target_language.addItems(langs_supported.values())
        self.web_preset.addItems([
            "English Wiktionary",
            "Monolingual Wiktionary",
            "Reverso Context",
            "Tatoeba",
            "Custom (Enter below)"
        ])
        self.bold_style.addItems([
            BoldStyles[1],
            BoldStyles[2],
            BoldStyles[0]
        ])
        self.gtrans_lang.addItems(langs_supported.values())
        super(GeneralTab, self).__init__()

    def load_dictionaries(self):
        custom_dicts = json.loads(settings.value("custom_dicts", '[]'))
        #self.postproc_selector.blockSignals(True)
        #self.postproc_selector.clear()
        dicts = getDictsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts
            )
        
        audio_dicts = getAudioDictsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts
        )
        self.all_audio_sources_widget.clear()
        self.all_audio_sources_widget.addItems(audio_dicts)

        self.all_sources_widget.clear()
        self.all_sources_widget.addItems(dicts)
        
        #self.postproc_selector.addItems(dicts)
        #self.postproc_selector.blockSignals(False)

    def load_freq_sources(self):
        custom_dicts = json.loads(settings.value("custom_dicts", '[]'))
        sources = getFreqlistsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts)
        self.freq_source.blockSignals(True)
        self.freq_source.clear()
        self.freq_source.addItem("<disabled>")
        for item in sources:
            self.freq_source.addItem(item)
        self.freq_source.setCurrentText(
            settings.value(
                "freq_source", "<disabled>"))
        self.freq_source.blockSignals(False)
        

    def initWidgets(self) -> None:
        self.layout_.addRow(QLabel("<h3>General</h3>"))
        self.layout_.addRow(
            QLabel("Target language"),
            self.target_language)

        self.layout_.addRow(QLabel("Bold words"), self.bold_style)

        self.layout_.addRow(QLabel("Forvo audio format"), self.audio_format)
        self.layout_.addRow(QLabel("<i>◊ Choose mp3 for playing on iOS, "
                                   "but ogg may save space</i>"))
        self.layout_.addRow(QLabel("Frequency list"), self.freq_source)
        self.layout_.addRow(self.lemfreq)
        self.layout_.addRow(
            QLabel("Google translate: To"),
            self.gtrans_lang)
        self.layout_.addRow(QLabel("Web lookup preset"), self.web_preset)
        self.layout_.addRow(QLabel("Custom URL pattern"), self.custom_url)
        self.layout_.addRow(self.importdict)
    
    def setupAutosave(self):
        self.load_freq_sources()
        self.register_config_handler(
            self.target_language,
            'target_language',
            'en',
            code_translate=True)
        self.register_config_handler(self.audio_format, 'audio_format', 'mp3')
        self.register_config_handler(self.lemfreq, 'lemfreq', True)

        self.bold_style.setCurrentText(BoldStyles[
            settings.value("bold_style", 1, type=int)])
        self.bold_style.currentTextChanged.connect(
            lambda t: settings.setValue(
                "bold_style", BoldStyles.index(t) if t in BoldStyles else 1))

        self.register_config_handler(
            self.gtrans_lang,
            'gtrans_lang',
            'en',
            code_translate=True)
        self.register_config_handler(
            self.freq_source, 'freq_source', '<disabled>')
        self.register_config_handler(
            self.web_preset,
            'web_preset',
            'English Wiktionary')
        self.register_config_handler(self.custom_url, 'custom_url', "https://en.wiktionary.org/wiki/@@@@")
        self.target_language.currentTextChanged.connect(self.load_dictionaries)
        self.target_language.currentTextChanged.connect(self.load_freq_sources)
        self.target_language.currentTextChanged.connect(self.load_url)
        self.web_preset.currentTextChanged.connect(self.load_url)
        self.gtrans_lang.currentTextChanged.connect(self.load_url)
        self.load_url()

    def load_url(self):
        lang = settings.value("target_language", "en")
        tolang = settings.value("gtrans_lang", "en")
        langfull = langcodes[lang]
        tolangfull = langcodes[tolang]
        presets = bidict({
                    "English Wiktionary": "https://en.wiktionary.org/wiki/@@@@#" + langfull,
                    "Monolingual Wiktionary": f"https://{lang}.wiktionary.org/wiki/@@@@",
                    "Reverso Context": f"https://context.reverso.net/translation/{langfull.lower()}-{tolangfull.lower()}/@@@@",
                    "Tatoeba": "https://tatoeba.org/en/sentences/search?query=@@@@"
                })
        
        if self.web_preset.currentText() == "Custom (Enter below)":
            self.custom_url.setEnabled(True)
            self.custom_url.setText(settings.value("custom_url"))
        else:
            self.custom_url.setEnabled(False)
            self.custom_url.setText(
                presets[self.web_preset.currentText()]
                )

    def dictmanager(self):
        importer = DictManager(self)
        importer.exec()
        self.load_dictionaries()
        self.load_freq_sources()
