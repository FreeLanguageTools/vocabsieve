from PyQt5.QtWidgets import (QFormLayout, QLabel, QLineEdit,
                             QSpinBox, QPushButton)
from .base_tab import BaseTab
from .fieldmatcher import FieldMatcher
from ..tools import findNotes, getVersion, guiBrowse
from ..global_names import settings, logger


class TrackingTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.getMatchedCards()

    def initWidgets(self):
        self.anki_query_mature = QLineEdit()
        self.mature_count_label = QLabel("")
        self.anki_query_young = QLineEdit()
        self.young_count_label = QLabel("")
        self.open_fieldmatcher = QPushButton("Match Fields (required for using Anki data)")

        self.preview_young_button = QPushButton("Preview in Anki Browser")
        self.preview_mature_button = QPushButton("Preview in Anki Browser")

        self.known_data_lifetime = QSpinBox()
        self.known_data_lifetime.setSuffix(" seconds")
        self.known_data_lifetime.setMinimum(0)
        self.known_data_lifetime.setMaximum(1000000)
        self.known_threshold = QSpinBox()
        self.known_threshold.setMinimum(1)
        self.known_threshold.setMaximum(1000)
        self.known_threshold_cognate = QSpinBox()
        self.known_threshold_cognate.setMinimum(1)
        self.known_threshold_cognate.setMaximum(1000)
        self.w_seen = QSpinBox()
        self.w_seen.setMinimum(0)
        self.w_seen.setMaximum(1000)
        self.w_lookup = QSpinBox()
        self.w_lookup.setMinimum(0)
        self.w_lookup.setMaximum(1000)
        self.w_anki_ctx = QSpinBox()
        self.w_anki_ctx.setMinimum(0)
        self.w_anki_ctx.setMaximum(1000)
        self.w_anki_word = QSpinBox()
        self.w_anki_word.setMinimum(0)
        self.w_anki_word.setMaximum(1000)
        self.w_anki_ctx_y = QSpinBox()
        self.w_anki_ctx_y.setMinimum(0)
        self.w_anki_ctx_y.setMaximum(1000)
        self.w_anki_word_y = QSpinBox()
        self.w_anki_word_y.setMinimum(0)
        self.w_anki_word_y.setMaximum(1000)
        self.known_langs = QLineEdit("en")
        self.known_langs.setToolTip(
            "Comma-separated list of languages that you know. These will be used to determine whether a word is cognate or not.")

    def setupWidgets(self):
        self.anki_query_mature.editingFinished.connect(self.getMatchedCards)
        self.anki_query_young.editingFinished.connect(self.getMatchedCards)
        self.preview_young_button.clicked.connect(self.previewYoung)
        self.preview_mature_button.clicked.connect(self.previewMature)
        self.open_fieldmatcher.clicked.connect(self.openFieldMatcher)

    def openFieldMatcher(self):
        fieldmatcher = FieldMatcher(self)
        fieldmatcher.exec()

    def getMatchedCards(self):
        if settings.value("enable_anki", True):
            try:
                api = settings.value('anki_api', 'http://127.0.0.1:8765')
                query_mature = self.anki_query_mature.text()
                mature_notes = findNotes(api, query_mature)
                self.mature_count_label.setText(f"Matched {str(len(mature_notes))} notes")
                query_young = self.anki_query_young.text()
                young_notes = findNotes(api, query_young)
                young_notes = [note for note in young_notes if note not in mature_notes]
                self.young_count_label.setText(f"Matched {str(len(young_notes))} notes")
            except Exception as e:
                logger.exception("Error while trying to find notes in Anki: " + repr(e))

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(QLabel("<h3>Anki tracking</h3>"))
        layout.addRow(QLabel("Use the Anki Card Browser to make a query string. "
                             "<br>Mature cards are excluded from the list of young cards automatically"))

        layout.addRow(QLabel("Query string for 'mature' cards"), self.anki_query_mature)
        layout.addRow(self.mature_count_label, self.preview_mature_button)
        layout.addRow(QLabel("Query string for 'young' cards"), self.anki_query_young)
        layout.addRow(self.young_count_label, self.preview_young_button)
        layout.addRow(self.open_fieldmatcher)
        layout.addRow(QLabel("<h3>Word scoring</h3>"))
        layout.addRow(QLabel("Known languages (use commas)"), self.known_langs)
        layout.addRow(QLabel("Known data lifetime"), self.known_data_lifetime)
        layout.addRow(QLabel("Known threshold score"), self.known_threshold)
        layout.addRow(QLabel("Known threshold score (cognate)"), self.known_threshold_cognate)
        layout.addRow(QLabel("Score: seen"), self.w_seen)
        layout.addRow(QLabel("Score: lookup (max 1 per day)"), self.w_lookup)
        layout.addRow(QLabel("Score: mature Anki target word"), self.w_anki_word)
        layout.addRow(QLabel("Score: mature Anki card context"), self.w_anki_ctx)
        layout.addRow(QLabel("Score: young Anki target word"), self.w_anki_word_y)
        layout.addRow(QLabel("Score: young Anki card context"), self.w_anki_ctx_y)

    def previewMature(self):
        try:
            _ = getVersion(api := settings.value('anki_api', 'http://127.0.0.1:8765'))
            guiBrowse(api, self.anki_query_mature.text())
        except Exception as e:
            logger.warning(repr(e))

    def previewYoung(self):
        try:
            _ = getVersion(api := settings.value('anki_api', 'http://127.0.0.1:8765'))
            guiBrowse(api, self.anki_query_young.text())
        except Exception as e:
            logger.warning(repr(e))

    def setupAutosave(self):

        self.register_config_handler(self.anki_query_mature, 'tracking/anki_query_mature', "prop:ivl>=14")
        self.register_config_handler(self.anki_query_young, 'tracking/anki_query_young', "prop:ivl<14 is:review")
        self.register_config_handler(self.known_threshold, 'tracking/known_threshold', 100)
        self.register_config_handler(self.known_threshold_cognate, 'tracking/known_threshold_cognate', 25)
        self.register_config_handler(self.known_langs, 'tracking/known_langs', 'en')
        self.register_config_handler(self.w_seen, 'tracking/w_seen', 8)
        self.register_config_handler(self.w_lookup, 'tracking/w_lookup', 15)
        self.register_config_handler(self.w_anki_word, 'tracking/w_anki_word', 70)
        self.register_config_handler(self.w_anki_ctx, 'tracking/w_anki_ctx', 30)
        self.register_config_handler(self.w_anki_word_y, 'tracking/w_anki_word_y', 40)
        self.register_config_handler(self.w_anki_ctx_y, 'tracking/w_anki_ctx_y', 20)
        self.register_config_handler(self.known_data_lifetime, 'tracking/known_data_lifetime', 1800)
