from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QPushButton, QCheckBox, \
                        QStatusBar, QMenuBar, QListView, QListWidget, \
                        QSizePolicy, QApplication, QLineEdit
from PyQt5.QtGui import  QFocusEvent, QDesktopServices
from PyQt5.QtCore import QUrl, QCoreApplication, pyqtSignal, Qt

from vocabsieve.ui.multi_definition_widget import MultiDefinitionWidget

from ..global_names import app_title, settings, datapath

from ..audio_player import AudioPlayer
from ..db import Record
from .searchable_boldable_text_edit import SearchableBoldableTextEdit
from .about import AboutDialog

import platform
import os
from typing import Optional


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
        self.audio_player = AudioPlayer()
        self.audio_fetched.connect(self.updateAudioUI)

        self.rec = Record(self, datapath)
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.audio_path = ""
        self.prev_clipboard = ""
        self.image_path = ""

        self.scaleFont()
        self.initWidgets()

        if self.settings.value("orientation", "Vertical") == "Vertical":
            self.resize(400, 730)
            self._layout = self.setupWidgetsV()  # type: ignore
        else:
            self.resize(1000, 300)
            self._layout = self.setupWidgetsH()  # type: ignore

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
        self.word.setPlaceholderText("Word will appear here when looked up.")
        self.definition = MultiDefinitionWidget()
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = MultiDefinitionWidget()
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Type in a list of tags to be used, separated by spaces (same as in Anki).")
        self.sentence.setToolTip(
            "Look up a word by double clicking it. Or, select it"
            ", then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton(f"Define direct [Shift-{MOD}-D]")
        self.lookup_exact_button.setToolTip(
            "This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}-S]")

        self.config_button = QPushButton("Configure..")
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
        self.freq_display = QLineEdit()
        self.freq_display.setPlaceholderText("Word frequency")

        self.discard_audio_button = QPushButton("Discard audio [Ctrl+Shift+X]")
        self.discard_audio_button.setToolTip("This will remove audio from the current working note.")
        self.audio_selector = QListWidget()
        self.audio_selector.setMinimumHeight(50)
        self.audio_selector.setFlow(QListView.TopToBottom)
        self.audio_selector.setResizeMode(QListView.Adjust)
        self.audio_selector.setWrapping(True)

        def play_audio_if_exists(x):
            if x is not None:
                self.play_audio(x.text()[2:])

        self.audio_selector.currentItemChanged.connect(play_audio_if_exists)
        self.audio_selector.itemDoubleClicked.connect(play_audio_if_exists)

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
        self.lookup_hist_label = QLabel("")


    def play_audio(self, x: Optional[str]) -> None:
        QCoreApplication.processEvents()
        if x is None:
            return

        self.audio_path = self.audio_player.play_audio(x, self.audios, self.settings.value("target_language", "en"))

    def updateAudioUI(self, audios):
        self.audios = audios
        self.audio_selector.clear()
        if len(self.audios):
            for item in self.audios:
                self.audio_selector.addItem("🔊 " + item)
            self.audio_selector.setCurrentItem(self.audio_selector.item(0))

    def setupWidgetsV(self) -> QGridLayout:
        """Prepares vertical layout"""

        layout = QGridLayout(self.widget)
        layout.addWidget(self.namelabel, 0, 0, 1, 2)

        layout.addWidget(self.single_word, 1, 0, 1, 2)
        layout.addWidget(self.lookup_definition_on_doubleclick, 2, 0, 1, 2)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 3, 0)
        layout.addWidget(self.read_button, 3, 1)
        layout.addWidget(self.image_viewer, 0, 2, 4, 1)
        layout.addWidget(self.sentence, 4, 0, 1, 3)
        layout.setRowStretch(4, 1)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 5, 0)

        if self.settings.value("lemmatization", True, type=bool):
            layout.addWidget(self.lookup_button, 5, 1)
            layout.addWidget(self.lookup_exact_button, 5, 2)
        else:
            layout.addWidget(self.lookup_button, 5, 1, 1, 2)

        layout.addWidget(self.word, 6, 0, 1, 2)
        layout.addWidget(self.lookup_hist_label, 6, 2)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 7, 0)
        layout.addWidget(self.freq_display, 7, 1)
        layout.addWidget(self.web_button, 7, 2)
        layout.setRowStretch(8, 2)
        layout.setRowStretch(10, 2)
        if self.settings.value("sg2_enabled", False, type=bool):
            layout.addWidget(self.definition, 8, 0, 2, 3)
            layout.addWidget(self.definition2, 10, 0, 2, 3)
        else:
            layout.addWidget(self.definition, 8, 0, 4, 3)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Pronunciation</h3>"),
            12,
            0,
            1,
            0)
        layout.addWidget(self.discard_audio_button, 12, 1, 1, 2, Qt.AlignRight)
        layout.addWidget(self.audio_selector, 13, 0, 1, 3)
        layout.setRowStretch(13, 1)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Additional tags</h3>"),
            14,
            0,
            1,
            3)

        layout.addWidget(self.tags, 15, 0, 1, 3)

        layout.addWidget(self.toanki_button, 16, 0, 1, 3)
        layout.addWidget(self.config_button, 17, 0, 1, 3)

        return layout

    

    def onHelp(self) -> None:
        url = f"https://wiki.freelanguagetools.org/vocabsieve_setup"
        QDesktopServices.openUrl(QUrl(url))

    def onAbout(self) -> None:
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()

    def setupWidgetsH(self) -> QGridLayout:
        """Prepares horizontal layout"""

        layout = QGridLayout(self.widget)
        # self.sentence.setMaximumHeight(99999)
        layout.addWidget(self.namelabel, 0, 0, 1, 1)
        layout.addWidget(self.image_viewer, 0, 1, 2, 1)
        layout.addWidget(self.single_word, 0, 3, 1, 1)
        layout.addWidget(self.lookup_definition_on_doubleclick, 0, 4, 1, 2)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 1, 0)
        layout.addWidget(self.freq_display, 0, 2)
        layout.addWidget(self.read_button, 6, 1)
        layout.addWidget(self.discard_audio_button, 6, 0)

        layout.addWidget(self.sentence, 2, 0, 3, 2)
        layout.addWidget(self.audio_selector, 5, 0, 1, 2)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 1, 2)

        layout.addWidget(self.lookup_button, 3, 2)
        layout.addWidget(self.lookup_exact_button, 4, 2)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 1, 3)
        layout.addWidget(self.web_button, 1, 4)
        layout.addWidget(self.word, 2, 2, 1, 1)
        if self.settings.value("dict_source2", "<disabled>") != "<disabled>":
            layout.addWidget(self.definition, 2, 3, 4, 1)
            layout.addWidget(self.definition2, 2, 4, 4, 1)
        else:
            layout.addWidget(self.definition, 2, 3, 4, 2)

        layout.addWidget(QLabel("Additional tags"), 5, 2, 1, 1)

        layout.addWidget(self.tags, 6, 2)

        layout.addWidget(self.toanki_button, 6, 3, 1, 1)
        layout.addWidget(self.config_button, 6, 4, 1, 1)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 5)
        layout.setColumnStretch(4, 5)
        layout.setRowStretch(0, 0)
        #layout.setRowStretch(1, 5)
        layout.setRowStretch(2, 5)
        layout.setRowStretch(3, 5)
        layout.setRowStretch(4, 5)
        layout.setRowStretch(5, 5)
        layout.setRowStretch(6, 0)

        return layout





    