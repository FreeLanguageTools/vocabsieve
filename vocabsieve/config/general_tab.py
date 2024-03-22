import json
from bidict import bidict
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QFormLayout
from PyQt5.QtCore import pyqtSignal
from .base_tab import BaseTab
from ..constants import langcodes
from .dictmanager import DictManager
from ..dictionary import getFreqlistsForLang, getDictsForLang, getAudioDictsForLang, langs_supported
from ..global_names import settings, logger

BOLD_STYLES = ["<disabled>", "Font weight", "Underscores"]


class GeneralTab(BaseTab):
    sources_reloaded_signal = pyqtSignal(list, list)

    def initWidgets(self):
        self.target_language = QComboBox()
        self.lemfreq = QCheckBox("Lemmatize before looking up frequency")
        self.lemfreq.setToolTip(
            "Lemmatize words before trying to find them in the frequency list." +
            "\nUse this for frequency lists displayed on FLT.org, but do not use it " +
            "\nfor frequency lists from Migaku. ")
        self.bold_word = QCheckBox("Bold selected word")
        self.audio_format = QComboBox()
        self.freq_source = QComboBox()
        self.gtrans_lang = QComboBox()
        self.web_preset = QComboBox()
        self.custom_url = QLineEdit()
        self.importdict = QPushButton('Manage local resources..')

    def setupWidgets(self) -> None:
        self.custom_url.setText("https://example.com/@@@@")
        self.audio_format.addItems(
            ['mp3', 'ogg']
        )
        self.custom_url.setEnabled(False)
        self.target_language.addItems(langs_supported.values())
        self.web_preset.addItems([
            "English Wiktionary",
            "Monolingual Wiktionary",
            "Reverso Context",
            "Tatoeba",
            "Custom (Enter below)"
        ])
        self.gtrans_lang.addItems(langs_supported.values())

        self.importdict.clicked.connect(self.dictmanager)

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(QLabel("<h3>General</h3>"))
        layout.addRow(
            QLabel("Target language"),
            self.target_language)

        layout.addRow(self.bold_word)

        layout.addRow(QLabel("Forvo audio format"), self.audio_format)
        layout.addRow(QLabel("<i>◊ Choose mp3 for playing on iOS, "
                             "but ogg may save space</i>"))
        layout.addRow(QLabel("Frequency list"), self.freq_source)
        layout.addRow(self.lemfreq)
        layout.addRow(
            QLabel("Google translate: To"),
            self.gtrans_lang)
        layout.addRow(QLabel("Web lookup preset"), self.web_preset)
        layout.addRow(QLabel("Custom URL pattern"), self.custom_url)
        layout.addRow(self.importdict)

    def load_dictionaries(self):
        custom_dicts = json.loads(settings.value("custom_dicts", '[]'))
        dicts = getDictsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts
        )

        audio_dicts = getAudioDictsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts
        )
        self.sources_reloaded_signal.emit(dicts, audio_dicts)

    def load_freq_sources(self):
        custom_dicts = json.loads(settings.value("custom_dicts", '[]'))
        sources = getFreqlistsForLang(
            langcodes.inverse[self.target_language.currentText()], custom_dicts)
        logger.info(
            "Loading frequency sources for language " +
            self.target_language.currentText() +
            ": " +
            str(sources))
        self.freq_source.blockSignals(True)
        self.freq_source.clear()
        self.freq_source.addItem("<disabled>")
        for item in sources:
            self.freq_source.addItem(item)
        self.freq_source.blockSignals(False)
        self.freq_source.setCurrentText(
            settings.value(
                "freq_source", "<disabled>"))

    def setupAutosave(self):
        self.register_config_handler(
            self.target_language,
            'target_language',
            'en',
            code_translate=True)
        self.register_config_handler(self.audio_format, 'audio_format', 'mp3')
        self.register_config_handler(self.lemfreq, 'lemfreq', True)

        self.register_config_handler(
            self.gtrans_lang,
            'gtrans_lang',
            'en',
            code_translate=True)
        self.register_config_handler(
            self.web_preset,
            'web_preset',
            'English Wiktionary')
        self.register_config_handler(self.bold_word, 'bold_word', True)
        self.register_config_handler(self.custom_url, 'custom_url', "https://en.wiktionary.org/wiki/@@@@")
        self.target_language.currentTextChanged.connect(self.load_dictionaries)
        self.target_language.currentTextChanged.connect(self.load_freq_sources)
        self.target_language.currentTextChanged.connect(self.load_url)
        self.web_preset.currentTextChanged.connect(self.load_url)
        self.gtrans_lang.currentTextChanged.connect(self.load_url)
        self.load_url()
        self.load_freq_sources()
        self.register_config_handler(
            self.freq_source, 'freq_source', '<disabled>')

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
