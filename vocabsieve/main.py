import csv
import importlib
import os
import platform
import sys
from datetime import datetime
from typing import Optional
import requests
from markdown import markdown
from packaging import version
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .app_text import *
QCoreApplication.setApplicationName(settings_app_title)
QCoreApplication.setOrganizationName(app_organization)
settings = QSettings(app_organization, settings_app_title)

from . import __version__
from .api import LanguageServer
from .config import *
from .db import *
from .dictionary import *
from .ext.importer import KoreaderImporter, KindleVocabImporter
from .ext.reader import ReaderServer
from .global_events import GlobalObject
from .text_manipulation import *
from .tools import *
from .ui.searchable_boldable_text_edit import SearchableBoldableTextEdit
from .ui.searchable_text_edit import SearchableTextEdit
from .constants import LookUpResults, DefinitionDisplayModes



Path(os.path.join(datapath, "images")).mkdir(parents=True, exist_ok=True)
# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text
if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"


class DictionaryWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_title(True))
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget = QWidget()
        self.settings = settings
        self.rec = Record(self)
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.audio_path = ""
        self.prev_clipboard = ""
        self.image_path = ""

        self.scaleFont()
        self.initWidgets()

        if self.settings.value("orientation", "Vertical") == "Vertical":
            self.resize(400, 700)
            self.layout = self.setupWidgetsV()  # type: ignore
        else:
            self.resize(1000, 300)
            self.layout = self.setupWidgetsH()  # type: ignore
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.initTimer()
        self.updateAnkiButtonState()
        self.setupShortcuts()
        self.checkUpdates()

        GlobalObject().addEventListener("double clicked", self.lookupClicked)
        if self.settings.value("primary", False, type=bool)\
                and QClipboard.supportsSelection(QApplication.clipboard()):
            QApplication.clipboard().selectionChanged.connect(
                lambda: self.clipboardChanged(False, True))
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

    def scaleFont(self) -> None:
        font = QApplication.font()
        font.setPointSize(
            int(font.pointSize() * self.settings.value("text_scale", type=int) / 100))
        self.setFont(font)

    def focusInEvent(self, event: QFocusEvent) -> None:
        if platform.system() == "Darwin":
            if self.prev_clipboard != QApplication.clipboard().text():
                self.clipboardChanged(evenWhenFocused=True)
            self.prev_clipboard = QApplication.clipboard().text()
        super().focusInEvent(event)

    def checkUpdates(self) -> None:
        if self.settings.value("check_updates") is None:
            answer = QMessageBox.question(
                self,
                "Check updates",
                "<h2>Would you like VocabSieve to check for updates automatically?</h2>"
                "Currently, the repository and releases are hosted on GitHub's servers, "
                "which will be queried for checking updates. <br>VocabSieve cannot and "
                "<strong>will not</strong> install any updates automatically."
                "<br>You can change this option in the configuration panel at a later date."
            )
            if answer == QMessageBox.Yes:
                self.settings.setValue("check_updates", True)
            if answer == QMessageBox.No:
                self.settings.setValue("check_updates", False)
            self.settings.sync()
        elif self.settings.value("check_updates", True, type=bool):
            try:
                res = requests.get("https://api.github.com/repos/FreeLanguageTools/vocabsieve/releases")
                data = res.json()
            except Exception:
                return
            latest_version = (current := data[0])['tag_name'].strip('v')
            current_version = importlib.metadata.version('vocabsieve')
            if version.parse(latest_version) > version.parse(current_version):
                answer2 = QMessageBox.information(
                    self,
                    "New version",
                    "<h2>There is a new version available!</h2>"
                    + f"<h3>Version {latest_version}</h3>"
                    + markdown(current['body']),
                    buttons=QMessageBox.Open | QMessageBox.Ignore
                )
                if answer2 == QMessageBox.Open:
                    QDesktopServices.openUrl(QUrl(current['html_url']))

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
        self.definition = SearchableTextEdit()
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = SearchableTextEdit()
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Type in a list of tags to be used, separated by spaces (same as in Anki).")
        self.sentence.setToolTip(
            "Look up a word by double clicking it. Or, select it"
            ", then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton(f"Define Direct [Shift-{MOD}-D]")
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

        self.web_button = QPushButton(f"Open webpage [{MOD}-1]")
        self.freq_display = QLineEdit()
        self.freq_display.setPlaceholderText("Word frequency")
        self.freq_display_lcd = QLCDNumber()
        self.freq_display_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.freq_display_lcd.display(0)

        self.audio_selector = QListWidget()
        self.audio_selector.setMinimumHeight(50)
        self.audio_selector.setFlow(QListView.TopToBottom)
        self.audio_selector.setResizeMode(QListView.Adjust)
        self.audio_selector.setWrapping(True)

        self.audio_selector.currentItemChanged.connect(lambda x: (
            self.play_audio(x.text()[2:]) if x is not None else None
        ))

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

        self.audio_path = play_audio(x, self.audios, self.settings.value("target_language", "en"))

    def setupWidgetsV(self) -> QGridLayout:
        """Prepares vertical layout"""

        layout = QGridLayout(self.widget)
        layout.addWidget(self.namelabel, 0, 0, 1, 2)

        layout.addWidget(self.single_word, 1, 0, 1, 3)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 2, 0)
        layout.addWidget(self.read_button, 2, 1)
        layout.addWidget(self.image_viewer, 0, 2, 3, 1)
        layout.addWidget(self.sentence, 3, 0, 1, 3)
        layout.setRowStretch(3, 1)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 4, 0)

        if self.settings.value("lemmatization", True, type=bool):
            layout.addWidget(self.lookup_button, 4, 1)
            layout.addWidget(self.lookup_exact_button, 4, 2)
        else:
            layout.addWidget(self.lookup_button, 4, 1, 1, 2)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 6, 0)
        layout.addWidget(self.freq_display, 6, 1)
        layout.addWidget(self.web_button, 6, 2)
        layout.addWidget(self.word, 5, 0, 1, 2)
        layout.addWidget(self.lookup_hist_label, 5, 2)
        layout.setRowStretch(7, 2)
        layout.setRowStretch(9, 2)
        if self.settings.value("dict_source2", "<disabled>") != "<disabled>":
            layout.addWidget(self.definition, 7, 0, 2, 3)
            layout.addWidget(self.definition2, 9, 0, 2, 3)
        else:
            layout.addWidget(self.definition, 7, 0, 4, 3)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Pronunciation</h3>"),
            11,
            0,
            1,
            3)
        layout.addWidget(self.audio_selector, 12, 0, 1, 3)
        layout.setRowStretch(12, 1)
        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Additional tags</h3>"),
            13,
            0,
            1,
            3)

        layout.addWidget(self.tags, 14, 0, 1, 3)

        layout.addWidget(self.toanki_button, 15, 0, 1, 3)
        layout.addWidget(self.config_button, 16, 0, 1, 3)

        return layout

    def setupButtons(self) -> None:
        self.lookup_button.clicked.connect(lambda: self.lookupClicked(True))
        self.lookup_exact_button.clicked.connect(
            lambda: self.lookupClicked(False))

        self.web_button.clicked.connect(self.onWebButton)

        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(True))

        self.sentence.textChanged.connect(self.updateAnkiButtonState)

        self.bar.addPermanentWidget(self.stats_label)

    def setupMenu(self) -> None:
        self.open_reader_action = QAction("&Reader")
        self.menu.addAction(self.open_reader_action)
        if not self.settings.value("reader_enabled", True, type=bool):
            self.open_reader_action.setEnabled(False)
        importmenu = self.menu.addMenu("&Import")
        exportmenu = self.menu.addMenu("&Export")
        helpmenu = self.menu.addMenu("&Help")
        self.help_action = QAction("&Help")
        self.about_action = QAction("&About")
        helpmenu.addAction(self.help_action)
        helpmenu.addAction(self.about_action)

        self.repeat_last_import_action = QAction("&Repeat last import")
        self.import_koreader_action = QAction("K&OReader highlights")
        self.import_kindle_new_action = QAction("K&indle lookups")

        self.export_notes_csv_action = QAction("Export &notes to CSV")
        self.export_lookups_csv_action = QAction("Export &lookup data to CSV")

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.repeat_last_import_action.triggered.connect(self.repeatLastImport)
        self.import_koreader_action.triggered.connect(self.importkoreader)
        self.import_kindle_new_action.triggered.connect(self.importkindleNew)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)

        importmenu.addActions(
            [
                self.repeat_last_import_action,
                self.import_koreader_action, 
                self.import_kindle_new_action,
            ]
        )

        exportmenu.addActions(
            [self.export_notes_csv_action, self.export_lookups_csv_action]
        )

        self.setMenuBar(self.menu)


    def exportNotes(self) -> None:
        """
        First ask for a file path, then save a CSV there.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV to file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-notes-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
            ),
            "CSV (*.csv)"
        )
        if not path:
            return
        
        with open(path, 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['timestamp', 'content', 'anki_export_success', 'sentence', 'word', 
                'definition', 'definition2', 'pronunciation', 'image', 'tags']
            )
            writer.writerows(self.rec.getAllNotes())

    def exportLookups(self) -> None:
        """
        First ask for a file path, then save a CSV there.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV to file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-lookups-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
            ),
            "CSV (*.csv)"
        )
        if not path:
            return

        with open(path, 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['timestamp', 'word', 'lemma', 'definition', 'language', 'lemmatize', 'dictionary', 'success']
            )
            writer.writerows(self.rec.getAllLookups())

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
        layout.addWidget(self.single_word, 0, 3, 1, 2)

        layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 1, 0)
        layout.addWidget(self.freq_display, 0, 2)
        layout.addWidget(self.read_button, 6, 1)

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

    def updateAnkiButtonState(self, forceDisable=False) -> None:  
        """Disables self.toanki_button if sentence field is empty"""

        if not self.sentence.toPlainText().strip() or forceDisable:
            self.toanki_button.setEnabled(False)
        else:
            self.toanki_button.setEnabled(True)

    def configure(self) -> None:
        api = self.settings.value('anki_api', 'http://127.0.0.1:8765')
        if self.settings.value('enable_anki', True, type=bool):
            try:
                _ = getVersion(api)
            except Exception as e:
                print(e)
                answer = QMessageBox.question(
                    self,
                    "Could not reach AnkiConnect",
                    "<h2>Could not reach AnkiConnect</h2>"
                    "AnkiConnect is required for changing Anki-related settings."
                    "<br>Choose 'Ignore' to not change Anki settings this time."
                    "<br>Choose 'Abort' to not open the configuration window."
                    "<br><br>If you have AnkiConnect listening to a non-default port or address, "
                    "select 'Ignore and change the Anki API option on the Anki tab, and "
                    "reopen the configuration window."
                    "<br><br>If you do not wish to use Anki with this program, select 'Ignore' "
                    "and then uncheck the 'Enable Anki' checkbox on the Anki tab.",
                    buttons=QMessageBox.Ignore | QMessageBox.Abort,
                    defaultButton=QMessageBox.Ignore
                )
                if answer == QMessageBox.Ignore:
                    pass
                if answer == QMessageBox.Abort:
                    return

        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec()


    def importkindleNew(self):
        fname = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select your Kindle root (top-level) directory",
        )
        if not fname:
            return
        try:
            KindleVocabImporter(self, fname).exec()
        except ValueError:
            QMessageBox.warning(self, "No notes are found",
                "Check if you've picked the right directory: it should be your Kindle root folder")
        except Exception as e:
            QMessageBox.warning(self, "Something went wrong", "Error: "+str(e))

    def importkoreader(self) -> None:
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select the directory containing ebook files",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )
        if not path:
            return
        try:
            KoreaderImporter(self, path).exec()
        except ValueError:
            QMessageBox.warning(self, "No notes are found", 
                "Check if you've picked the right directory. It should be a folder containing all of your the ebooks you want to extract from")
        except Exception as e:
            QMessageBox.warning(self, "Something went wrong", "Error: "+str(e))

    def repeatLastImport(self):
        try:
            method = self.settings.value("last_import_method")
            path = self.settings.value("last_import_path")
            if not (method and path):
                QMessageBox.warning(self, "You have not imported notes before",
                    "Use any one of the other two options on the menu, and you will be able to use this one next time.")
                return
            if method == "kindle":
                KindleVocabImporter(self, path).exec()
            elif method == "koreader":
                KoreaderImporter(self, path).exec()
            else:
                # Nightly users, clear it for them
                self.settings.setValue("last_import_method", "") 
                self.settings.setValue("last_import_path", "") 
                QMessageBox.warning(self, "You have not imported notes before",
                    "Use any one of the other two options on the menu, and you will be able to use this one next time.")
        except Exception as e:
            print("Encountered error while repeating last import, aborting:", e)

    def setupShortcuts(self) -> None:
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.toanki_button.animateClick)
        self.shortcut_getdef_e = QShortcut(QKeySequence('Ctrl+Shift+D'), self)
        self.shortcut_getdef_e.activated.connect(self.lookup_exact_button.animateClick)
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.lookup_button.animateClick)
        self.shortcut_paste = QShortcut(QKeySequence('Ctrl+V'), self)
        self.shortcut_paste.activated.connect(self.read_button.animateClick)
        self.shortcut_web = QShortcut(QKeySequence('Ctrl+1'), self)
        self.shortcut_web.activated.connect(self.web_button.animateClick)

    def getCurrentWord(self) -> str:
        """Returns currently selected word. If there isn't any, last selected word is returned"""

        # defines word only if widget have focus on it
        for text_field in (self.sentence, self.definition, self.definition2):
            if text_field.hasFocus() and (selected_text := text_field.textCursor().selectedText().strip()):
                self.previousWord = selected_text
                return selected_text

        if not self.previousWord:
            self.previousWord = self.word.text().strip()
        return self.previousWord

    def onWebButton(self) -> None:
        """Shows definitions of self.word.text() in wiktionoary in browser"""

        url = self.settings.value("custom_url", f"https://en.wiktionary.org/wiki/{self.word.text()}")
        QDesktopServices.openUrl(QUrl(url))

    def onReaderOpen(self) -> None:
        """Opens reader in browser"""

        url = f"http://{self.settings.value('reader_host', '127.0.0.1', type=str)}:{self.settings.value('reader_port', '39285', type=str)}"
        QDesktopServices.openUrl(QUrl(url))

    def lookupClicked(self, use_lemmatize=True) -> None:
        target = self.getCurrentWord()
        self.updateAnkiButtonState()
        if target:
            self.lookupSet(target, use_lemmatize)

    def setState(self, state: LookUpResults) -> None:
        self.word.setText(state['word'])
        self.definition.original = state['definition']
        display_mode1 = self.settings.value(
            self.settings.value("dict_source", "Wiktionary (English)")
            + "/display_mode",
            "Markdown"
        )
        skip_top1 = self.settings.value(
            self.settings.value("dict_source", "Wiktionary (English)")
            + "/skip_top",
            0, type=int
        )
        collapse_newlines1 = self.settings.value(
            self.settings.value("dict_source", "Wiktionary (English)")
            + "/collapse_newlines",
            0, type=int
        )

        self.definition.setText(
            process_definition(
                state['definition'].strip(),
                display_mode1,
                skip_top1,
                collapse_newlines1
            )
        )

        if state.get('definition2'):
            self.definition2.original = state['definition2']
            display_mode2 = self.settings.value(
                self.settings.value("dict_source2", "Wiktionary (English)")
                + "/display_mode",
                "Markdown"
            )
            skip_top2 = self.settings.value(
                self.settings.value("dict_source2", "Wiktionary (English)")
                + "/skip_top",
                0, type=int
            )
            collapse_newlines2 = self.settings.value(
                self.settings.value("dict_source2", "Wiktionary (English)")
                + "/collapse_newlines",
                0, type=int
            )
            if display_mode2 in ['Raw', 'Plaintext', 'Markdown']:
                self.definition2.setPlainText(
                    process_definition(
                        state['definition2'].strip(),
                        display_mode2,
                        skip_top2,
                        collapse_newlines2)
                )
            else:
                self.definition2.setHtml(
                    process_definition(
                        state['definition2'].strip(),
                        display_mode2,
                        skip_top2,
                        collapse_newlines2)
                )

        cursor = self.sentence.textCursor()
        cursor.clearSelection()
        self.sentence.setTextCursor(cursor)

    def setSentence(self, content) -> None:
        self.sentence.setText(str.strip(content))

    def setWord(self, content) -> None:
        self.word.setText(content)

    def setImage(self, content: Optional[QPixmap]) -> None:
        if content is None:
            self.image_viewer.setPixmap(QPixmap())
            self.image_viewer.setText("<center><b>&lt;No image selected&gt;</center>")
            self.image_path = ""
            return
        
        filename = str(int(time.time()*1000)) + '.' + self.settings.value("img_format", "jpg")
        self.image_path = os.path.join(datapath, "images", filename)
        content.save(
            self.image_path, quality=self.settings.value("img_quality", -1, type=int)
        )
        self.image_viewer.setPixmap(content)

    def clipboardChanged(self, evenWhenFocused=False, selection=False):
        """
        If the input is just a single word, we look it up right away.
        If it's a json and has the required fields, we use these fields to
        populate the relevant fields.
        Otherwise we dump everything to the Sentence field.
        By default this is not activated when the window is in focus to prevent
        mistakes, unless it is used from the button.
        """
        if selection:
            text = QApplication.clipboard().text(QClipboard.Selection)
        else:
            # I am not sure how you can copy an image to PRIMARY
            # so here we go
            if QApplication.clipboard().mimeData().hasImage():
                self.setImage(QApplication.clipboard().pixmap())
                return
            
            text = QApplication.clipboard().text()

        lang = self.settings.value("target_language", "en")
        if self.isActiveWindow() and not evenWhenFocused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            target = re.sub('[\\?\\.!«»…()\\[\\]]*', "", target)
            self.previousWord = target
            sentence = preprocess_clipboard(copyobj['sentence'], lang)
            self.setSentence(sentence)
            self.setWord(target)
            self.lookupSet(target)
        elif self.single_word.isChecked() and is_oneword(preprocess_clipboard(text, lang)):
            self.setSentence(word := preprocess_clipboard(text, lang))
            self.setWord(word)
            self.lookupSet(text)
        else:
            self.setSentence(preprocess_clipboard(text, lang))

    def lookupSet(self, word, use_lemmatize=True) -> None:
        sentence_text = self.sentence.unboldedText

        if settings.value("bold_style", type=int):
            # Bold word that was clicked on, either with "<b>{word}</b>" or 
            # "__{word}__".

            if self.settings.value("bold_style", type=int) == 1:
                apply_bold = apply_bold_tags
            elif self.settings.value("bold_style", type=int) == 2:
                apply_bold = apply_bold_char
            else:
                print(f"BoldStyle={self.settings.value('bold_style', type=int)} is not implemented")

            sentence_text = bold_word_in_text(
                word, 
                sentence_text, 
                apply_bold,
                self.getLanguage(), 
                use_lemmatize, 
                self.getLemGreedy())

        self.sentence.setHtml(sentence_text)

        QCoreApplication.processEvents()
        result = self.lookup(word, use_lemmatize)
        self.setState(result)
        past_lookups_count = self.rec.countLemmaLookups(word, self.settings.value("target_language",'en'))
        if past_lookups_count <= 1:
            self.lookup_hist_label.setText("<b>new word</b>")
        else:
            self.lookup_hist_label.setText(f"<b>{past_lookups_count} prev. lookups</b>")
        QCoreApplication.processEvents()
        self.audio_path = ""

        if self.settings.value("audio_dict", "Forvo (all)") == "<disabled>":
            return

        try:
            self.audios = getAudio(
                word,
                self.settings.value("target_language", 'en'),
                dictionary=self.settings.value("audio_dict", "Forvo (all)"),
                custom_dicts=json.loads(
                    self.settings.value("custom_dicts", '[]')))
        except Exception:
            self.audios = {}
        
        self.audio_selector.clear()

        if len(self.audios):
            for item in self.audios:
                self.audio_selector.addItem("🔊 " + item)
            self.audio_selector.setCurrentItem(
                self.audio_selector.item(0)
            )

    def getLanguage(self) -> str:
        return self.settings.value("target_language", "en")  # type: ignore

    def getLemGreedy(self) -> bool:
        return self.settings.value("lem_greedily", False, type=bool)  # type: ignore

    def lookup(self, word: str, use_lemmatize: bool, recordDate: Optional[float] = None) -> LookUpResults:
        """
        Look up a word and return a dict with the lemmatized form (if enabled)
        and definition
        """
        if not recordDate:
            recordDate = time.time()
        word = re.sub('[«»…,()\\[\\]_]*', "", word)
        # TODO
        # why manually check "lemmatization" in settings when you can pass it through parameter?
        lemmatize = use_lemmatize and self.settings.value(
            "lemmatization", True, type=bool)
        lem_greedily = self.getLemGreedy()
        lemfreq = self.settings.value("lemfreq", True, type=bool)
        short_sign = "Y" if lemmatize else "N"
        language = self.getLanguage()
        TL = language  # Handy synonym
        gtrans_lang: str = self.settings.value("gtrans_lang", "en")
        dictname: str = self.settings.value("dict_source", "Wiktionary (English)")
        freqname: str = self.settings.value("freq_source", "<disabled>")
        if freqname != "<disabled>":
            freq_found = False
            freq_display = self.settings.value("freq_display", "Rank")
            try:
                freq, max_freq = getFreq(word, language, lemfreq, freqname)
                freq_found = True
            except TypeError:
                pass

            if freq_found:
                if freq_display == "Rank":
                    self.freq_display.setText(f'{str(freq)}/{str(max_freq)}')
                elif freq_display == "Stars":
                    self.freq_display.setText(freq_to_stars(freq, lemfreq))
            else:
                if freq_display == "Rank":
                    self.freq_display.setText('-1')
                elif freq_display == "Stars":
                    self.freq_display.setText(freq_to_stars(1e6, lemfreq))
        self.status(
            f"L: '{word}' in '{language}', lemma: {short_sign}, from {dictionaries.get(dictname, dictname)}")
        try:
            item = lookupin(
                word,
                language,
                lemmatize,
                lem_greedily,
                dictname,
                gtrans_lang,
                self.settings.value("gtrans_api", "https://lingva.ml"))
            self.rec.recordLookup(
                word,
                item['definition'],
                TL,
                lemmatize,
                dictname,
                True, recordDate)
        except Exception as e:
            self.status(str(e))
            self.rec.recordLookup(
                word, "", TL, lemmatize, dictname, False, recordDate)
            self.updateAnkiButtonState(True)
            item = {
                "word": word,
                "definition": failed_lookup(word, self.settings)
            }
            return item
        dict2name = self.settings.value("dict_source2", "<disabled>")
        if dict2name == "<disabled>":
            return item
        try:
            item2: LookUpResults = lookupin(
                word,
                language,
                lemmatize,
                lem_greedily,
                dict2name,
                gtrans_lang)
            self.rec.recordLookup(
                word,
                item2['definition'],
                TL,
                lemmatize,
                dict2name,
                True, recordDate)
        except Exception as e:
            self.status("Dict-2 failed" + str(e))
            self.rec.recordLookup(
                word, "", TL, lemmatize, dict2name, False, recordDate)
            self.definition2.clear()
            return item
        return {
            "word": item['word'],
            'definition': item['definition'],
            'definition2': item2['definition']}

    def createNote(self) -> None:
        sentence = self.sentence.textBoldedByTags.replace("\n", "<br>")

        tags = (self.settings.value("tags", "vocabsieve").strip() + " " + self.tags.text().strip()).split(" ")
        word = self.word.text()
        content = {
            "deckName": self.settings.value("deck_name"),
            "modelName": self.settings.value("note_type"),
            "fields": {
                self.settings.value("sentence_field"): sentence,
                self.settings.value("word_field"): word,
            },
            "tags": tags
        }
        definition = self.process_defi_anki(
            self.definition,
            self.settings.value(
                self.settings.value("dict_source", "Wiktionary (English)")
                + "/display_mode",
                "Markdown"
            )
        )
        content['fields'][self.settings.value('definition_field')] = definition
        definition2 = None
        if self.settings.value("dict_source2", "<disabled>") != '<disabled>':
            try:
                if self.settings.value(
                    "definition2_field",
                        "<disabled>") == "<disabled>":
                    self.warn(
                        "Aborted.\nYou must have field for Definition#2 in order to use two dictionaries.")
                    return
                definition2 = self.process_defi_anki(
                    self.definition2,
                    self.settings.value(
                        self.settings.value("dict_source2", "Wiktionary (English)")
                        + "/display_mode",
                        "Markdown"
                    )
                )
                content['fields'][self.settings.value(
                    'definition2_field')] = definition2
            except Exception as e:
                return

        if self.settings.value(
            "pronunciation_field",
                "<disabled>") != '<disabled>' and self.audio_path:
            content['audio'] = {
                "path": self.audio_path,
                "filename": os.path.basename(self.audio_path),
                "fields": [
                    self.settings.value("pronunciation_field")
                ]
            }
            self.audio_selector.clear()
        if self.settings.value("image_field", "<disabled>") != '<disabled>' and self.image_path:
            content['picture'] = {
                "path": self.image_path,
                "filename": os.path.basename(self.image_path),
                "fields": [
                    self.settings.value("image_field")
                ]
            }

        self.status("Adding note")
        api = self.settings.value("anki_api")
        enable_anki_flag = self.settings.value("enable_anki", True, type=bool)
        try:
            if enable_anki_flag:
                addNote(api, content)

            self.rec.recordNote(
                    json.dumps(content), 
                    sentence,
                    word,
                    definition,
                    definition2,
                    self.audio_path,
                    self.image_path,
                    " ".join(tags),
                    enable_anki_flag
                    )

            self.sentence.clear()
            self.word.clear()
            self.definition.clear()
            self.definition2.clear()
            self.status(f"Note added: '{word}'")
        except Exception as e:
            self.rec.recordNote(
                json.dumps(content), 
                sentence,
                word,
                definition,
                definition2,
                self.audio_path,
                self.image_path,
                " ".join(tags),
                False
            )
            self.status(f"Failed to add note: {word}")
            QMessageBox.warning(
                self,
                f"Failed to add note: {word}",
                "<h2>Failed to add note</h2>"
                + f"Error: {str(e)}"
                + "\nHints: AnkiConnect must be running to add notes."
                "<br>If you wish to only add notes to the database (and "
                "export it as CSV), click Configure and uncheck 'Enable"
                " Anki' on the Anki tab."

            )
        self.setImage(None)

    def process_defi_anki(self, 
                          w: SearchableTextEdit, 
                          display_mode: DefinitionDisplayModes) -> str:
        """Process definitions before sending to Anki"""

        print("display mode is", display_mode)
        if display_mode in ["Raw", "Plaintext"]:
            return w.toPlainText().replace("\n", "<br>") # Anki needs <br>s
        elif display_mode == "Markdown":
            return markdown_nop(w.toPlainText())
        elif display_mode == "Markdown-HTML":
            return markdown_nop(w.toMarkdown())
        elif display_mode == "HTML":
            return w.original  # type: ignore
        else:
            return ""

    def errorNoConnection(self, error) -> None:
        """
        Dialog window sent when something goes wrong in configuration step
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Error")
        msg.setInformativeText(
            str(error) +
            "\n\nHints:" +
            "\nAnkiConnect must be running in order to add notes." +
            "\nIf you have AnkiConnect running at an alternative endpoint," +
            "\nbe sure to change it in the configuration.")
        msg.exec()

    def initTimer(self) -> None:
        self.showStats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showStats)
        self.timer.start(2000)

    def showStats(self) -> None:
        lookups = self.rec.countLookupsToday()
        notes = self.rec.countNotesToday()
        self.stats_label.setText(f"L:{str(lookups)} N:{str(notes)}")

    def time(self) -> str:
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def status(self, msg: str) -> None:
        self.bar.showMessage(self.time() + " " + msg, 4000)

    def warn(self, text: str) -> None:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(text)
        msg.exec()

    def startServer(self) -> None:
        if self.settings.value("api_enabled", True, type=bool):
            try:
                self.thread = QThread()
                port = self.settings.value("port", 39284, type=int)
                host = self.settings.value("host", "127.0.0.1")
                self.worker = LanguageServer(self, host, port)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.start_api)
                self.worker.note_signal.connect(self.onNotepyqtSignal)
                self.thread.start()
            except Exception as e:
                print(e)
                self.status("Failed to start API server")
        
        if self.settings.value("reader_enabled", True, type=bool):
            try:
                self.thread2 = QThread()
                port = self.settings.value("reader_port", 39285, type=int)
                host = self.settings.value("reader_host", "127.0.0.1")
                self.worker2 = ReaderServer(self, host, port)
                self.worker2.moveToThread(self.thread2)
                self.thread2.started.connect(self.worker2.start_api)
                self.thread2.start()
            except Exception as e:
                print(e)
                self.status("Failed to start reader server")

    def onNotepyqtSignal(
            self,
            sentence: str,
            word: str,
            definition: str,
            tags: list) -> None:
        self.setSentence(sentence)
        self.setWord(word)
        self.definition.setText(definition)
        self.tags.setText(" ".join(tags))
        self.createNote()


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About VocabSieve")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = QLabel(
            f'''
VocabSieve version: {__version__}<br>
Python version: {sys.version}<br>
PyQt5 (Qt bindings) version: {importlib.metadata.version('PyQT5')}<br><br>
© 2022 FreeLanguageTools<br><br>
Visit <a href="https://wiki.freelanguagetools.org">FreeLanguageTools Wiki</a> for more info on how to use this tool.<br>
You can also talk to us on <a href="https://webchat.kde.org/#/room/#flt:midov.pl">Matrix</a>
or <a href="https://t.me/fltchat">Telegram</a> for support.<br><br>

Consult <a href="https://wiki.freelanguagetools.org/vocabsieve_dicts">this wiki page</a>
to find compatible dictionaries. <br><br>

VocabSieve (formerly SSM, ssmtool) is free software available to you under the terms of
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.
If you found a bug, or have enhancement ideas, please open an issue on the
Github <a href=https://github.com/FreeLanguageTools/vocabsieve>repository</a>.<br><br>

This program is yours to keep. There is no EULA you need to agree to.
No usage data is sent to any server other than the configured dictionary APIs.
Statistics data are stored locally.
<br><br>
If you find this tool useful, you can give it a star on Github and tell others about it. Any suggestions will also be appreciated.
            '''
        )
        message.setTextFormat(Qt.RichText)
        message.setOpenExternalLinks(True)
        message.setWordWrap(True)
        message.adjustSize()
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


def main():
    app = QApplication(sys.argv)
    w = DictionaryWindow()

    w.show()
    sys.exit(app.exec())
