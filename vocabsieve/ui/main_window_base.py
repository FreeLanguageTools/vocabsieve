from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QPushButton, QCheckBox, \
                        QStatusBar, QMenuBar, \
                        QSizePolicy, QApplication, QLineEdit
from PyQt5.QtGui import  QFocusEvent, QDesktopServices
from PyQt5.QtCore import QUrl, pyqtSignal, Qt
from .audio_selector import AudioSelector

from .multi_definition_widget import MultiDefinitionWidget
from .word_record_display import WordRecordDisplay

from ..global_names import app_title, settings, datapath

from ..record import Record
from ..local_dictionary import LocalDictionary
from .searchable_boldable_text_edit import SearchableBoldableTextEdit
from .freq_display_widget import FreqDisplayWidget
from .about import AboutDialog
from ..models import AnkiSettings, WordActionWeights

import platform
import os
from sentence_splitter import SentenceSplitter


# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text
if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"

class MainWindowBase(QMainWindow):
    audio_fetched = pyqtSignal(dict)
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_title(True))
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget = QWidget()
        self.settings = settings
        self.rec = Record(self, datapath)
        self.dictdb = LocalDictionary(datapath)
        self.splitter = SentenceSplitter(language=self.settings.value("target_language", "en"))
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.audio_path = ""
        self.prev_clipboard = ""
        self.image_path = ""

        self.scaleFont()
        self.initWidgets()

        self.resize(500, 800)
        self.setupWidgetsV() 

    def scaleFont(self) -> None:
        font = QApplication.font()
        font.setPointSize(
            int(font.pointSize() * self.settings.value("text_scale", type=int) / 100))
        self.setFont(font)

    def focusInEvent(self, event: QFocusEvent) -> None:
        if platform.system() == "Darwin" or (platform.system().startswith("Linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland"):
            if self.prev_clipboard != QApplication.clipboard().text() and len(QApplication.clipboard().text()):
                self.clipboardChanged(evenWhenFocused=True)
            self.prev_clipboard = QApplication.clipboard().text()
        super().focusInEvent(event)

    def clipboardChanged(self, evenWhenFocused=False, selection=False) -> None:
        pass


    def initWidgets(self) -> None:
        self.namelabel = QLabel(
            "<h2 style=\"font-weight: normal;\">" + app_title(False) + "</h2>")
        self.menu = QMenuBar(self)
        self.sentence = SearchableBoldableTextEdit()
        self.sentence.setPlaceholderText(
            "Sentence copied to the clipboard will show up here.")
        self.sentence.setMinimumHeight(50)
        #self.sentence.setMaximumHeight(300)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Word")
        self.src_name_label = QLabel()
        self.definition = MultiDefinitionWidget(self.word)
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = MultiDefinitionWidget()
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Tags to be used, separated by spaces")
        self.sentence.setToolTip(
            "Look up a word by double clicking it. Or, select it"
            ", then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton(f"Define direct [Shift-{MOD}-D]")
        self.lookup_exact_button.setToolTip(
            "This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}-S]")

        self.read_button = QPushButton(f"Read clipboard [{MOD}-V]")
        self.bar = QStatusBar()
        self.setStatusBar(self.bar)
        self.stats_label = QLabel()

        self.single_word = QCheckBox("Single word lookups")
        self.single_word.setToolTip(
            "If enabled, vocabsieve will act as a quick dictionary and look up any single words copied to the clipboard.\n"
            "This can potentially send your clipboard contents over the network if an online dictionary service is used.\n"
            "This is INSECURE if you use password managers that copy passwords to the clipboard.")
        self.lookup_definition_on_doubleclick = QCheckBox(
            "Lookup definition on double click")
        self.lookup_definition_on_doubleclick.setToolTip(
            "Disable this if you want to use 3rd party dictionaries with copied text (e.g. with mpvacious).")
        self.lookup_definition_on_doubleclick.clicked.connect(lambda v: self.settings.setValue("lookup_definition_on_doubleclick", v))
        self.lookup_definition_on_doubleclick.setChecked(self.settings.value("lookup_definition_on_doubleclick", True, type=bool))

        self.web_button = QPushButton(f"Open webpage [{MOD}-1]")
        self.freq_widget = FreqDisplayWidget()
        self.freq_widget.setPlaceholderText("Word frequency")

        self.audio_selector = AudioSelector(self.settings)
        
        self.definition.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition2.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition.setPlaceholderText(
            'Look up a word by double clicking it. Or, select it, then press "Get definition".')
        self.definition2.setPlaceholderText(
            'Look up a word by double clicking it. Or, select it, then press "Get definition".')

        self.image_viewer = QLabel("<center><b>&lt;No image selected&gt;</center>")
        self.image_viewer.setScaledContents(True)
        self.image_viewer.setToolTip(f"{MOD}-I to clear the image.")
        self.image_viewer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_viewer.setStyleSheet(
            '''
                border: 1px solid black;
            '''
        )
        self.word_record_display = WordRecordDisplay()



    def setupWidgetsV(self) -> None:
        """Prepares vertical layout"""

        layout = QGridLayout(self.widget)
        layout.addWidget(self.namelabel, 0, 0, 1, 2)

        layout.addWidget(self.single_word, 1, 0, 1, 2)
        layout.addWidget(self.lookup_definition_on_doubleclick, 2, 0, 1, 2)

        layout.addWidget(self.read_button, 3, 0)
        layout.addWidget(self.web_button, 3, 1)
        layout.addWidget(self.image_viewer, 0, 2, 4, 1)
        layout.addWidget(self.sentence, 4, 0, 1, 3)
        layout.setRowStretch(4, 1)
        

        layout.addWidget(self.word, 5, 0)
        layout.addWidget(self.freq_widget, 5, 1)
        layout.addWidget(self.word_record_display, 5, 2)
        
        layout.setRowStretch(6, 2)
        layout.setRowStretch(8, 2)
        if self.settings.value("sg2_enabled", False, type=bool):
            layout.addWidget(self.definition, 6, 0, 2, 3)
            layout.addWidget(self.definition2, 8, 0, 2, 3)
        else:
            layout.addWidget(self.definition, 6, 0, 4, 3)

        layout.addWidget(self.audio_selector, 11, 0, 1, 3)
        layout.setRowStretch(11, 1)

        layout.addWidget(self.tags, 12, 0, 1, 3)

        layout.addWidget(self.toanki_button, 13, 0, 1, 3)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 5)

    

    def onHelp(self) -> None:
        url = f"https://wiki.freelanguagetools.org/vocabsieve_setup"
        QDesktopServices.openUrl(QUrl(url))

    def onAbout(self) -> None:
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()


    
    def getAnkiSettings(self) -> AnkiSettings:
        return AnkiSettings(
            deck=self.settings.value("deck_name", "Default"),
            model=self.settings.value("note_type", "vocabsieve-notes"),
            word_field=self.settings.value("word_field", "Word"),
            sentence_field=self.settings.value("sentence_field", "Sentence"),
            definition1_field=self.settings.value("definition1_field", "Definition"),
            definition2_field=self.settings.value("definition2_field"),
            audio_field=self.settings.value("pronunciation_field"),
            image_field=self.settings.value("image_field"),
        )

    def getWordActionWeights(self) -> WordActionWeights:
        return WordActionWeights(
            seen=self.settings.value("tracking/w_seen", 8, type=int),
            lookup=self.settings.value("tracking/w_lookup", 15, type=int),
            anki_mature_ctx=self.settings.value("tracking/w_anki_ctx", 30, type=int),
            anki_mature_tgt=self.settings.value("tracking/w_anki_word", 70, type=int),
            anki_young_ctx=self.settings.value("tracking/w_anki_ctx_y", 20, type=int),
            anki_young_tgt=self.settings.value("tracking/w_anki_word_y", 40, type=int),
            threshold=self.settings.value("tracking/known_threshold", 100, type=int),
            threshold_cognate=self.settings.value("tracking/known_threshold_cognate", 25, type=int)
        )




    