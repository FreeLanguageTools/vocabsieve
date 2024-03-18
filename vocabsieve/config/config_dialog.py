from PyQt5.QtWidgets import (QDialog, QStatusBar, QCheckBox, QComboBox, QLineEdit,
                             QSpinBox, QPushButton, QSlider, QLabel, QHBoxLayout,
                             QWidget, QTabWidget, QMessageBox, QColorDialog, QListWidget,
                             QFormLayout, QGridLayout, QVBoxLayout
                             )
from PyQt5.QtGui import QImageWriter
from PyQt5.QtCore import Qt, pyqtSlot
import platform
import qdarktheme
from shutil import rmtree

from ..fieldmatcher import FieldMatcher
from ..ui import SourceGroupWidget, AllSourcesWidget
from ..models import DisplayMode, FreqDisplayMode, LemmaPolicy
from loguru import logger
from ..tools import (addDefaultModel, getVersion, findNotes,
                     guiBrowse, getDeckList,
                     getNoteTypes, getFields
                     )
from .general_tab import GeneralTab
from .source_tab import SourceTab
from .processing_tab import ProcessingTab
from .anki_tab import AnkiTab
from .network_tab import NetworkTab
from ..global_names import settings

import os


class ConfigDialog(QDialog):
    def __init__(self, parent, ):
        super().__init__(parent)
        logger.debug("Initializing settings dialog")
        self.parent = parent
        self.resize(700, 500)
        self.setWindowTitle("Configure VocabSieve")
        logger.debug("Initializing widgets for settings dialog")
        self.initWidgets()
        self.initTabs()
        logger.debug("Setting up widgets")
        self.setupWidgets()
        logger.debug("Setting up autosave")
        self.setupAutosave()
        logger.debug("Setting up processing")
        logger.debug("Fetching matched cards from AnkiConnect")
        self.getMatchedCards()
        logger.debug("Got matched cards")

    def initWidgets(self):
        self.status_bar = QStatusBar()
        self.allow_editing = QCheckBox(
            "Allow directly editing definition fields")
        self.primary = QCheckBox("*Use primary selection")
        self.register_config_handler(self.allow_editing, "allow_editing", True)
        self.capitalize_first_letter = QCheckBox(
            "Capitalize first letter of sentence")
        self.capitalize_first_letter.setToolTip(
            "Capitalize the first letter of clipboard's content before pasting into the sentence field. Does not affect dictionary lookups.")

        #self.orientation = QComboBox()
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

        self.reset_button = QPushButton("Reset settings")
        self.reset_button.setStyleSheet('QPushButton {color: red;}')
        self.nuke_button = QPushButton("Delete data")
        self.nuke_button.setStyleSheet('QPushButton {color: red;}')

        self.img_format = QComboBox()
        self.img_format.addItems(
            ['png', 'jpg', 'gif', 'bmp']
        )
        supported_img_formats = list(map(lambda s: bytes(s).decode(), QImageWriter.supportedImageFormats()))
        # WebP requires a plugin, which is commonly but not always installed
        if 'webp' in supported_img_formats:
            self.img_format.addItem('webp')

        self.img_quality = QSpinBox()
        self.img_quality.setMinimum(-1)
        self.img_quality.setMaximum(100)

        self.freq_display_mode = QComboBox()
        self.freq_display_mode.addItems([
            FreqDisplayMode.stars,
            FreqDisplayMode.rank
        ])

        self.anki_query_mature = QLineEdit()
        self.mature_count_label = QLabel("")
        self.anki_query_young = QLineEdit()
        self.young_count_label = QLabel("")

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

        self.theme = QComboBox()
        self.theme.addItems(qdarktheme.get_themes())
        self.theme.addItem("system")

        self.accent_color = QPushButton()
        self.accent_color.setText(settings.value("accent_color", "default"))
        self.accent_color.setToolTip("Hex color code (e.g. #ff0000 for red)")
        self.accent_color.clicked.connect(self.save_accent_color)

        self.known_langs = QLineEdit("en")
        self.known_langs.setToolTip(
            "Comma-separated list of languages that you know. These will be used to determine whether a word is cognate or not.")

        self.open_fieldmatcher = QPushButton("Match fields (required for using Anki data)")

    def initTabs(self):
        self.tabs = QTabWidget()
        # block signals
        self.tab_g = GeneralTab()  # General
        self.tab_s = SourceTab()  # Sources
        self.tab_g.sources_reloaded_signal.connect(self.tab_s.reloadSources)
        self.tab_s.sg2_visibility_changed.connect(self.changeMainLayout)
        self.tab_p = ProcessingTab()  # Processing
        self.tab_g.sources_reloaded_signal.connect(self.tab_p.setupSelector)
        self.tab_a = AnkiTab()  # Anki
        self.tab_n = NetworkTab()  # Network
        self.tab_i = QWidget()  # Interface
        self.tab_i_layout = QFormLayout(self.tab_i)
        self.tab_m = QWidget()  # Miscellaneous
        self.tab_m_layout = QFormLayout(self.tab_m)
        self.tab_t = QWidget()  # Tracking
        self.tab_t_layout = QFormLayout(self.tab_t)
        self.tab_g.load_dictionaries()

        self.tabs.resize(400, 400)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.tabs)
        self._layout.addWidget(self.status_bar)

        self.tabs.addTab(self.tab_g, "General")
        self.tabs.addTab(self.tab_s, "Sources")
        self.tabs.addTab(self.tab_p, "Processing")
        self.tabs.addTab(self.tab_a, "Anki")
        self.tabs.addTab(self.tab_n, "Network")
        self.tabs.addTab(self.tab_t, "Tracking")
        self.tabs.addTab(self.tab_i, "Interface")
        self.tabs.addTab(self.tab_m, "Misc")

    def save_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid() and settings.value("theme") != "system":
            settings.setValue("accent_color", color.name())
            self.accent_color.setText(color.name())
            qdarktheme.setup_theme(
                settings.value("theme", "dark"),
                custom_colors={"primary": color.name()}
            )

    def reset_settings(self):
        answer = QMessageBox.question(
            self,
            "Confirm Reset<",
            "<h1>Danger!</h1>"
            "Are you sure you want to reset all settings? "
            "This action cannot be undone. "
            "This will also close the configuration window.",
            defaultButton=QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.Yes:
            settings.clear()
            self.close()

    def nuke_profile(self):
        datapath = self.parent.datapath
        answer = QMessageBox.question(
            self,
            "Confirm Reset",
            "<h1>Danger!</h1>"
            "Are you sure you want to delete all user data? "
            "The following directory will be deleted:<br>" + datapath
            + "<br>This action cannot be undone. "
            "This will also close the program.",
            defaultButton=QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.Yes:
            settings.clear()
            rmtree(datapath)
            os.mkdir(datapath)
            self.parent.close()

    def setupWidgets(self):

        self.tab_i_layout.addRow(
            QLabel("<h3>Interface settings</h3>")
        )
        self.tab_i_layout.addRow(
            QLabel("<h4>Settings marked * require a restart to take effect.</h4>"))
        if platform.system() == "Linux":
            # Primary selection is only available on Linux
            self.tab_i_layout.addRow(self.primary)
        self.tab_i_layout.addRow("Theme", self.theme)
        self.tab_i_layout.addRow(QLabel('<i>◊ Changing to "system" requires a restart.</i>'))
        self.tab_i_layout.addRow("Accent color", self.accent_color)
        self.tab_i_layout.addRow(self.allow_editing)
        self.tab_i_layout.addRow(QLabel("Frequency display mode"), self.freq_display_mode)
        #self.tab_i_layout.addRow(QLabel("*Interface layout orientation"), self.orientation)
        self.tab_i_layout.addRow(QLabel("*Text scale"), self.text_scale_box)

        self.text_scale.valueChanged.connect(
            lambda _: self.text_scale_label.setText(
                format(
                    self.text_scale.value() / 100,
                    "1.2f") + "x"))

        self.tab_m_layout.addRow(self.capitalize_first_letter)
        self.tab_m_layout.addRow(QLabel("<h3>Images</h3>"))
        self.tab_m_layout.addRow(QLabel("Image format"), self.img_format)
        self.tab_m_layout.addRow(QLabel("<i>◊ WebP, JPG, GIF are lossy, which create smaller files.</i>"))
        self.tab_m_layout.addRow(QLabel("Image quality"), self.img_quality)
        self.tab_m_layout.addRow(QLabel("<i>◊ Between 0 and 100. -1 uses the default value from Qt.</i>"))
        self.tab_m_layout.addRow(QLabel("<h3>Reset</h3>"))
        self.tab_m_layout.addRow(QLabel("Your data will be lost forever! There is NO cloud backup."))
        self.tab_m_layout.addRow(QLabel("<strong>Reset all settings to defaults</strong>"), self.reset_button)
        self.tab_m_layout.addRow(QLabel("<strong>Delete all user data</strong>"), self.nuke_button)

        self.tab_t_layout.addRow(QLabel("<h3>Anki tracking</h3>"))
        self.tab_t_layout.addRow(QLabel("Use the Anki Card Browser to make a query string. "
                                        "<br>Mature cards are excluded from the list of young cards automatically"))

        self.tab_t_layout.addRow(QLabel("Query string for 'mature' cards"), self.anki_query_mature)
        self.tab_t_layout.addRow(self.mature_count_label, self.preview_mature_button)
        self.tab_t_layout.addRow(QLabel("Query string for 'young' cards"), self.anki_query_young)
        self.tab_t_layout.addRow(self.young_count_label, self.preview_young_button)
        self.tab_t_layout.addRow(self.open_fieldmatcher)
        self.tab_t_layout.addRow(QLabel("<h3>Word scoring</h3>"))
        self.tab_t_layout.addRow(QLabel("Known languages (use commas)"), self.known_langs)
        self.tab_t_layout.addRow(QLabel("Known data lifetime"), self.known_data_lifetime)
        self.tab_t_layout.addRow(QLabel("Known threshold score"), self.known_threshold)
        self.tab_t_layout.addRow(QLabel("Known threshold score (cognate)"), self.known_threshold_cognate)
        self.tab_t_layout.addRow(QLabel("Score: seen"), self.w_seen)
        self.tab_t_layout.addRow(QLabel("Score: lookup (max 1 per day)"), self.w_lookup)
        self.tab_t_layout.addRow(QLabel("Score: mature Anki target word"), self.w_anki_word)
        self.tab_t_layout.addRow(QLabel("Score: mature Anki card context"), self.w_anki_ctx)
        self.tab_t_layout.addRow(QLabel("Score: young Anki target word"), self.w_anki_word_y)
        self.tab_t_layout.addRow(QLabel("Score: young Anki card context"), self.w_anki_ctx_y)

        self.reset_button.clicked.connect(self.reset_settings)
        self.nuke_button.clicked.connect(self.nuke_profile)

    def getMatchedCards(self):
        if settings.value("enable_anki", True):
            try:
                _ = getVersion(api := settings.value('anki_api', 'http://127.0.0.1:8765'))
                query_mature = self.anki_query_mature.text()
                mature_notes = findNotes(api, query_mature)
                self.mature_count_label.setText(f"Matched {str(len(mature_notes))} notes")
                query_young = self.anki_query_young.text()
                young_notes = findNotes(api, query_young)
                young_notes = [note for note in young_notes if note not in mature_notes]
                self.young_count_label.setText(f"Matched {str(len(young_notes))} notes")
            except Exception:
                pass

    def setupAutosave(self):
        if settings.value("config_ver") is None \
                and settings.value("target_language") is not None:
            # if old config is copied to new location, nuke it
            settings.clear()
        settings.setValue("config_ver", 1)

        self.register_config_handler(self.freq_display_mode, "freq_display", "Stars (like Migaku)")
        self.register_config_handler(self.allow_editing, 'allow_editing', True)
        self.register_config_handler(self.primary, 'primary', False)
        #self.register_config_handler(
        #    self.orientation, 'orientation', 'Vertical')
        self.register_config_handler(self.text_scale, 'text_scale', '100')

        self.register_config_handler(self.capitalize_first_letter, 'capitalize_first_letter', False)
        self.register_config_handler(self.img_format, 'img_format', 'jpg')
        self.register_config_handler(self.img_quality, 'img_quality', -1)

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

        self.register_config_handler(self.theme, 'theme', 'auto' if platform.system() !=
                                     "Linux" else 'system')  # default to native on Linux

        # Using the previous qdarktheme.setup_theme function would result in having
        # the default accent color when changing theme. Instead, using the setupTheme
        # function does not change the current accent color.
        self.theme.currentTextChanged.connect(self.setupTheme)
        self.anki_query_mature.editingFinished.connect(self.getMatchedCards)
        self.anki_query_young.editingFinished.connect(self.getMatchedCards)
        self.preview_young_button.clicked.connect(self.previewYoung)
        self.preview_mature_button.clicked.connect(self.previewMature)
        self.open_fieldmatcher.clicked.connect(self.openFieldMatcher)

    def openFieldMatcher(self):
        fieldmatcher = FieldMatcher(self)
        fieldmatcher.exec()

    def setupTheme(self) -> None:
        theme = self.theme.currentText()  # auto, dark, light, system
        if theme == "system":
            return
        accent_color = self.accent_color.text()
        if accent_color == "default":  # default is not a color
            qdarktheme.setup_theme(
                theme=theme
            )
        else:
            qdarktheme.setup_theme(
                theme=theme,
                custom_colors={"primary": accent_color},
            )

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

    def errorNoConnection(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(
            str(error) + "\nAnkiConnect must be running to set Anki-related options."
            "\nIf you have AnkiConnect set up at a different endpoint, set that now "
            "and reopen the config tool.")
        msg.exec()

    @pyqtSlot(bool)
    def changeMainLayout(self, checked: bool):
        if checked:
            # This means user has changed from one source to two source mode,
            # need to redraw main window
            if settings.value("orientation", "Vertical") == "Vertical":
                self.parent._layout.removeWidget(self.parent.definition)
                self.parent._layout.addWidget(
                    self.parent.definition, 6, 0, 2, 3)
                self.parent._layout.addWidget(
                    self.parent.definition2, 8, 0, 2, 3)
                self.parent.definition2.setVisible(True)
        else:
            self.parent._layout.removeWidget(self.parent.definition)
            self.parent._layout.removeWidget(self.parent.definition2)
            self.parent.definition2.setVisible(False)
            self.parent._layout.addWidget(self.parent.definition, 6, 0, 4, 3)

    def status(self, msg):
        self.status_bar.showMessage(self.parent.time() + " " + msg, 4000)

    def register_config_handler(self, *args, **kwargs):  # pylint: disable=unused-argument
        logger.error("register_config_handler is being called!")
