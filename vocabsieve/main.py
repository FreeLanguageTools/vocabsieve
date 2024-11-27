import csv
import dataclasses
import importlib.metadata
import os
import sys
import time
import re
from datetime import datetime
from typing import Optional, cast
import requests
from packaging import version
import platform
import json
from loguru import logger

from markdown import markdown
from PyQt5.QtCore import QCoreApplication, QStandardPaths, QTimer, QDateTime, QThread, QUrl, pyqtSlot, QThreadPool, pyqtSignal, Qt
from PyQt5.QtGui import QClipboard, QKeySequence, QPixmap, QDesktopServices, QImage, QTextCursor
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QShortcut, QFileDialog

import qdarktheme

from .global_names import datapath, lock, app, settings  # First local import
from .analyzer import BookAnalyzer
from .config import ConfigDialog
from .stats import StatisticsWindow
from .dictionary import preprocess_clipboard
from .local_dictionary import dictdb
from .importer import KindleVocabImporter, KoreaderVocabImporter, AutoTextImporter, WordListImporter
from .reader import ReaderServer
from .contentmanager import ContentManager
from .tools import (
    compute_word_score,
    failCards,
    is_json,
    make_audio_source_group,
    modelFieldNames,
    prepareAnkiNoteDict,
    is_oneword,
    addNote,
    findNotes,
    guiBrowse,
    make_dict_source,
    getVersion,
    make_freq_source,
    remove_punctuations,
    unix_milliseconds_to_datetime_str,
    apply_word_rules)
from .ui import MainWindowBase, WordMarkingDialog
from .models import (AudioSourceGroup, KnownMetadata, LookupRecord, SRSNote, TrackingDataError,
                     WordRecord, LookupTrigger)
from .lemmatizer import lem_word
from .uncaught_hook import ExceptionCatcher


class MainWindow(MainWindowBase):
    got_updates = pyqtSignal(list)
    polled_clipboard_changed = pyqtSignal()
    polled_selection_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.catcher = ExceptionCatcher()
        self.datapath = datapath
        self.thread_manager = QThreadPool()
        self.known_data: Optional[dict[str, WordRecord]] = None
        self.known_metadata: Optional[KnownMetadata] = None
        self.known_data_timestamp: float = 0
        self.last_got_focus: float = time.time()
        self.last_target_word_id: int = -1
        self.last_added_note_id: int = -1
        self.previous_word: str = ""
        self.previous_trigger: LookupTrigger = LookupTrigger.double_clicked
        self.pause_polling: bool = False
        self.cognates: set[str] = set()
        app.applicationStateChanged.connect(self.onApplicationStateChanged)
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.setupShortcuts()
        self.checkUpdatesOnThread()
        self.initSources()
        self.initTimers()
        self.got_updates.connect(self.gotUpdatesInfo)

        self.setupClipboardMonitor()
        self.setMinimumWidth(settings.value("minimum_width", 550, type=int))

        if not settings.value("internal/configured"):
            self.configure()
            settings.setValue("internal/configured", True)

    def onApplicationStateChanged(self, state):
        if state == Qt.ApplicationActive:
            self.last_got_focus = time.time()

    def setupClipboardMonitor(self):
        self.sentence.double_clicked.connect(self.lookup)
        self.sentence.hovered_over.connect(self.lookupHovered)
        self.definition.double_clicked.connect(self.lookup)
        self.definition2.double_clicked.connect(self.lookup)
        cant_listen_to_clipboard = (os.environ.get("XDG_SESSION_TYPE") == "wayland"
                                    or platform.system() == "Darwin")
        if settings.value("primary", False, type=bool) and QClipboard.supportsSelection(QApplication.clipboard()):
            QApplication.clipboard().selectionChanged.connect(
                lambda: self.clipboardChanged(selection=True))
        if not cant_listen_to_clipboard:
            QApplication.clipboard().dataChanged.connect(self.clipboardChanged)
        else:
            logger.info("Clipboard monitoring is not supported on Wayland and MacOS, will poll instead")
            self.initPollingClipboard()
            self.polled_clipboard_changed.connect(self.clipboardChanged)
            self.polled_selection_changed.connect(lambda: self.clipboardChanged(selection=True))

    def initPollingClipboard(self):
        self.last_clipboard: str = QApplication.clipboard().text()
        self.last_selection: str = ""
        if QApplication.clipboard().supportsSelection():
            self.last_selection = QApplication.clipboard().text(QClipboard.Selection)
        self.last_image: Optional[QImage] = None
        clipboard_timer = QTimer(self)
        clipboard_timer.timeout.connect(self.pollClipboard)
        clipboard_timer.start(50)

    def pollClipboard(self):
        if self.pause_polling:
            return
        mimedata = QApplication.clipboard().mimeData()
        if mimedata.hasImage():
            if self.last_image is None or self.last_image != QApplication.clipboard().image():
                self.last_image = QApplication.clipboard().image()
                logger.debug(f"Polling: Clipboard image changed")
                self.polled_clipboard_changed.emit()
        elif mimedata.hasText():
            if QApplication.clipboard().text() != self.last_clipboard and QApplication.clipboard().text().strip() != "":
                self.last_clipboard = QApplication.clipboard().text()
                logger.debug(f"Polling: Clipboard text changed to '''{self.last_clipboard}'''")
                self.polled_clipboard_changed.emit()
        if QApplication.clipboard().supportsSelection() and settings.value("primary", False, type=bool):
            if self.last_selection != QApplication.clipboard().text(QClipboard.Selection) \
                    and QApplication.clipboard().text(QClipboard.Selection) != self.last_clipboard \
                    and QApplication.clipboard().text(QClipboard.Selection).strip() != "":
                self.last_selection = QApplication.clipboard().text(QClipboard.Selection)
                logger.debug(f"Polling: Primary selction changed to '''{self.last_selection}'''")
                self.polled_selection_changed.emit()

    def initSources(self):
        logger.debug("Initializing sources")
        sg1_src_names = json.loads(settings.value("sg1", '[]'))
        self.sg1 = []
        for src_name in sg1_src_names:
            self.sg1.append(make_dict_source(src_name))
        self.definition.setSourceGroup(self.sg1)
        logger.debug(f"Source Group 1: {sg1_src_names} has been created.")

        if settings.value("freq_source", "<disabled>") != "<disabled>":
            self.freq_widget.setSource(make_freq_source(settings.value("freq_source")))

        if settings.value("sg2_enabled", False, type=bool):
            sg2_src_names = json.loads(settings.value("sg2", '[]'))
            logger.debug(f"Source Group 2: {sg2_src_names} has been created.")
            self.sg2 = []
            for src_name in sg2_src_names:
                self.sg2.append(make_dict_source(src_name))
        else:
            logger.debug("Source Group 2 is disabled, emptying source widget.")
            self.sg2 = []

        self.definition2.setSourceGroup(self.sg2)

        if audio_src_list := json.loads(settings.value("audio_sg", '[]')):
            self.audio_sg = make_audio_source_group(audio_src_list)
            logger.debug(f"Audio source group: {audio_src_list} has been created")
        else:
            logger.debug("Audio source group is empty, emptying audio source widget.")
            self.audio_sg = AudioSourceGroup([])
        self.audio_selector.setSourceGroup(self.audio_sg)

    @pyqtSlot()
    def checkUpdatesOnThread(self) -> None:
        print("Started checking updates")
        if settings.value("check_updates") is None:
            answer = QMessageBox.question(
                None,
                "Check updates",
                "<h2>Would you like VocabSieve to check for updates automatically on launch?</h2>"
                "Currently, the repository and releases are hosted on GitHub's servers, "
                "which will be queried for checking updates. <br>VocabSieve cannot and "
                "<strong>will not</strong> install any updates automatically."
                "<br>You can change this option in the configuration panel at any time."
            )
            if answer == QMessageBox.Yes:
                settings.setValue("check_updates", True)
            if answer == QMessageBox.No:
                settings.setValue("check_updates", False)
            settings.sync()
        if settings.value("check_updates", True, type=bool):
            self.thread_manager.start(self.checkUpdates)
        print("Finished checking updates")

    def checkUpdates(self) -> None:
        res = requests.get("https://api.github.com/repos/FreeLanguageTools/vocabsieve/releases", timeout=5)
        data = res.json()
        self.got_updates.emit(data)

    def gotUpdatesInfo(self, data: dict) -> None:
        latest_version = (current := data[0])['tag_name'].strip('v')
        current_version = importlib.metadata.version('vocabsieve')
        if version.parse(latest_version) > version.parse(current_version):
            answer2 = QMessageBox.information(
                None,
                "New version",
                "<h2>There is a new version available!</h2>"
                + f"<h3>Version {latest_version}</h3>"
                + markdown(current['body']),
                buttons=QMessageBox.Open | QMessageBox.Ignore
            )
            if answer2 == QMessageBox.Open:
                QDesktopServices.openUrl(QUrl(current['html_url']))

    def setupButtons(self) -> None:
        self.web_button.clicked.connect(self.onWebButton)

        self.toanki_button.clicked.connect(self.createNote)
        self.view_last_note_button.clicked.connect(self.viewLastNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(even_when_focused=True))

        self.status_bar.addPermanentWidget(self.stats_label)

    def setupMenu(self) -> None:
        readermenu = self.menu.addMenu("&Reader")
        configmenu = self.menu.addMenu("&Configure")
        importmenu = self.menu.addMenu("&Import")
        recordmenu = self.menu.addMenu("&Track")
        exportmenu = self.menu.addMenu("&Export")
        analyzemenu = self.menu.addMenu("A&nalyze")
        statsmenu = self.menu.addMenu("S&tatistics")
        helpmenu = self.menu.addMenu("&Help")

        self.open_reader_action = QAction("&Reader")
        self.set_book_path_action = QAction("Set book path")
        self.config_action = QAction("&Configure")
        self.config_action.setMenuRole(QAction.PreferencesRole)
        self.stats_action = QAction("S&tatistics")
        self.help_action = QAction("&Setup guide")
        self.help_action.setMenuRole(QAction.ApplicationSpecificRole)
        self.about_action = QAction("&About")
        self.content_manager_action = QAction("Content Manager")
        self.analyze_book_action = QAction("Analyze book")
        self.mark_words_action = QAction("Mark words from frequency list")
        self.export_known_words_action = QAction("Export known words to JSON")
        self.export_word_scores_action = QAction("Export word scores to JSON")
        self.open_logs_action = QAction("View session logs")
        self.open_data_folder_action = QAction("Open data folder")

        if not settings.value("reader_enabled", True, type=bool):
            self.open_reader_action.setEnabled(False)
            self.set_book_path_action.setEnabled(False)

        readermenu.addAction(self.open_reader_action)
        readermenu.addAction(self.set_book_path_action)
        configmenu.addAction(self.config_action)
        statsmenu.addAction(self.stats_action)
        helpmenu.addAction(self.help_action)
        helpmenu.addAction(self.about_action)
        helpmenu.addAction(self.open_logs_action)
        helpmenu.addAction(self.open_data_folder_action)
        recordmenu.addAction(self.content_manager_action)
        recordmenu.addAction(self.mark_words_action)
        analyzemenu.addAction(self.analyze_book_action)

        self.repeat_last_import_action = QAction("&Repeat last import")
        self.import_koreader_vocab_action = QAction("K&OReader vocab builder")
        self.import_kindle_vocab_action = QAction("K&indle lookups")
        self.import_auto_text_action = QAction("Auto import from text")
        self.import_wordlist_action = QAction("Import word list from file")

        self.export_notes_csv_action = QAction("Export &notes to CSV")
        self.export_lookups_csv_action = QAction("Export &lookup data to CSV")

        self.content_manager_action.triggered.connect(self.onContentManager)

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_logs_action.triggered.connect(self.onOpenLogs)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.set_book_path_action.triggered.connect(self.onSetBookPath)
        self.config_action.triggered.connect(self.configure)
        self.repeat_last_import_action.triggered.connect(self.repeatLastImport)
        self.import_koreader_vocab_action.triggered.connect(self.importKoreader)
        self.import_kindle_vocab_action.triggered.connect(self.importKindle)
        self.import_wordlist_action.triggered.connect(self.importWordlist)
        self.import_auto_text_action.triggered.connect(self.importAutoText)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)
        self.stats_action.triggered.connect(self.onStats)
        self.analyze_book_action.triggered.connect(self.onAnalyzeBook)
        self.export_known_words_action.triggered.connect(self.exportKnownWords)
        self.export_word_scores_action.triggered.connect(self.exportWordData)
        self.mark_words_action.triggered.connect(self.markWords)
        self.open_data_folder_action.triggered.connect(self.onOpenDataFolder)

        importmenu.addActions(
            [
                self.repeat_last_import_action,
                self.import_koreader_vocab_action,
                self.import_kindle_vocab_action,
                self.import_auto_text_action,
                self.import_wordlist_action
            ]
        )

        exportmenu.addActions(
            [
                self.export_notes_csv_action,
                self.export_lookups_csv_action,
                self.export_known_words_action,
                self.export_word_scores_action
            ]
        )

        self.setMenuBar(self.menu)

    def markWords(self):
        if settings.value("freq_source", "<disabled>") == "<disabled>":
            self.warn("No frequency source is set. Please set a frequency source in the configuration dialog.")
            return
        if not settings.value("lemfreq", False, type=bool):
            self.warn("Marking words requires a lemmatized frequency list to work properly.")
            return
        if self.known_data is None:
            self.warnKnownDataNotReady()
            return
        words = self.freq_widget.getAllWords()
        dialog = WordMarkingDialog(self, words)
        dialog.exec()

    def onOpenDataFolder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(datapath))

    def onSetBookPath(self):
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select a directory containing your books",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )
        if path:
            settings.setValue("books_dir", path)
            settings.sync()

    def onAnalyzeBook(self):
        if self.checkAnkiConnect() and self.known_data is not None:
            path = QFileDialog.getOpenFileName(
                parent=self,
                caption="Select book",
                filter="Ebook files (*.epub *.fb2 *.mobi *.html *.azw *.azw3 *.kfx)",
                directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
            )[0]
            if path:
                BookAnalyzer(self, path).open()
        elif self.known_data is None:
            self.warnKnownDataNotReady()

    def getKnownWords(self) -> tuple[list[str], list[str]]:
        if self.known_data is not None:
            langcode = settings.value('target_language', 'en')
            known_threshold = settings.value('tracking/known_threshold', 100, type=int)
            known_threshold_cognate = settings.value('tracking/known_threshold_cognate', 25, type=int)
            known_words: list[str] = []
            known_cognates: list[str] = []
            self.cognates = set()
            if dictdb.hasCognatesData():
                known_langs = settings.value('tracking/known_langs', 'en').split(",")
                self.cognates = dictdb.getCognatesData(langcode, known_langs)
            waw = self.getWordActionWeights()
            for word, word_record in self.known_data.items():
                score = compute_word_score(word_record, waw)
                if score >= known_threshold:
                    known_words.append(word)
                elif (score >= known_threshold_cognate) and (word in self.cognates):
                    known_words.append(word)
                    known_cognates.append(word)
            return known_words, known_cognates
        else:
            return [], []

    def exportKnownWords(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save known words to JSON file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-known-words-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"
            ),
            "JSON (*.json)"
        )
        if not path:
            return
        if self.known_data is None:
            self.warnKnownDataNotReady()
            return
        known_words, _ = self.getKnownWords()
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(known_words, file, indent=4, ensure_ascii=False)

    def checkDataAvailability(self) -> TrackingDataError:
        # Check is Anki enabled
        # Can proceed is anki is disabled
        if not settings.value("enable_anki", True, type=bool):
            return TrackingDataError.no_errors
        # Anki is enabled
        # Check if AnkiConnect is running
        if not self.checkAnkiConnect() == 1:
            return TrackingDataError.anki_enabled_but_not_running
        # AnkiConnect is running
        # Check if fieldmap is set
        fieldmap = json.loads(settings.value("tracking/fieldmap", "{}"))
        if not fieldmap:
            return TrackingDataError.anki_enabled_running_but_no_fieldmap
        # fieldmap is set
        return TrackingDataError.no_errors

    @pyqtSlot()
    def getKnownDataOnThread(self) -> None:
        if self.checkDataAvailability() != TrackingDataError.no_errors:
            logger.debug("Some data sources aren't available, not getting known data now")
            return
        self.thread_manager.start(self._refreshKnownData)

    @pyqtSlot()
    def _refreshKnownData(self) -> None:
        with lock:
            self.known_data, self.known_metadata = self.rec.getKnownData()
            self.known_data_timestamp = time.time()
            self.status("Known data is ready")

    def exportWordData(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save word scores to JSON file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-word-scores-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"
            ),
            "JSON (*.json)"
        )
        if not path:
            return
        if self.known_data is None:
            self.warnKnownDataNotReady()
            return
        with open(path, 'w', encoding='utf-8') as file:
            json.dump([dataclasses.asdict(item)
                      for item in self.known_data.values()], file, indent=4, ensure_ascii=False)

    def onContentManager(self):
        ContentManager(self).exec()

    def onStats(self):
        if self.checkAnkiConnect() and self.known_data is not None:
            stats_window = StatisticsWindow(self)
            stats_window.open()
        elif self.known_data is None:
            self.warnKnownDataNotReady()

    def warnKnownDataNotReady(self):
        QMessageBox.warning(
            self,
            "Known data is not ready",
            "Known data is not ready yet. Please try again in a few seconds, and make sure AnkiConnect is available if Anki support is enabled."
        )

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
                ['timestamp', 'word', 'lemma', 'language', 'lemmatize', 'dictionary', 'success']
            )
            writer.writerows(self.rec.getAllLookups())

    def onHelp(self) -> None:
        url = f"https://docs.freelanguagetools.org/"
        QDesktopServices.openUrl(QUrl(url))

    def checkAnkiConnect(self) -> int:
        api = settings.value('anki_api', 'http://127.0.0.1:8765')
        if settings.value('enable_anki', True, type=bool):
            try:
                _ = getVersion(api)
                return 1
            except Exception as e:
                print(repr(e))
                answer = QMessageBox.question(
                    self,
                    "Could not reach AnkiConnect",
                    "<h2>Could not reach AnkiConnect</h2>"
                    "AnkiConnect is required for changing Anki-related settings or viewing statistics."
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
                    return 2
                else:
                    return 0
        else:
            return 3

    def configure(self) -> None:
        # Prevent clipboard monitoring while settings are open
        self.pause_polling = True
        logger.debug("Opening settings dialog")
        if self.checkAnkiConnect():
            settings_dialog = ConfigDialog(self)
            settings_dialog.exec()
            self.initSources()
        self.pause_polling = False

    def importKindle(self):
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
            QMessageBox.warning(self, "Something went wrong", "Error: " + repr(e))

    def importAutoText(self) -> None:
        path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select book or text file",
            filter="Book, text files (*.epub *.fb2 *.mobi *.html *.azw *.azw3 *.kfx *.txt)",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )[0]
        if path:
            AutoTextImporter(self, path).exec()

    def importKoreader(self) -> None:
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select a directory containing KOReader settings and ebook files",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )
        if not path:
            return
        try:
            KoreaderVocabImporter(self, path).exec()
        except ValueError:
            QMessageBox.warning(
                self,
                "No notes are found",
                "Check if you've picked the right directory. It should be a folder containing both all of your books and KOReader settings.")
        except Exception as e:
            QMessageBox.warning(self, "Something went wrong", "Error: " + repr(e))

    def importWordlist(self) -> None:
        path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a UTF-8 encoded word list file, where words are separated by newlines",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )[0]
        if path:
            with open(path, 'r', encoding='utf-8') as file:
                words = file.read().splitlines()
                WordListImporter(self, words).exec()

    def repeatLastImport(self):
        method = settings.value("last_import_method")
        path = settings.value("last_import_path")
        if not (method and path):
            QMessageBox.warning(
                self,
                "You have not imported notes before",
                "Use any one of the other two options on the menu, and you will be able to use this one next time.")
            return
        if method == "kindle":
            KindleVocabImporter(self, path).exec()
        elif method == "koreader-vocab":
            KoreaderVocabImporter(self, path).exec()
        else:
            # Nightly users, clear it for them
            settings.setValue("last_import_method", "")
            settings.setValue("last_import_path", "")
            QMessageBox.warning(
                self,
                "You have not imported notes before",
                "Use any one of the other two options on the menu, and you will be able to use this one next time.")

    def setupShortcuts(self) -> None:
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.toanki_button.animateClick)
        self.shortcut_double_click_toggle = QShortcut(QKeySequence('Ctrl+2'), self)
        self.shortcut_double_click_toggle.activated.connect(self.lookup_definition_on_doubleclick.animateClick)
        self.shortcut_view_note = QShortcut(QKeySequence('Ctrl+F'), self)
        self.shortcut_view_last_note = QShortcut(QKeySequence('Ctrl+Shift+F'), self)
        self.shortcut_view_last_note.activated.connect(self.view_last_note_button.animateClick)
        self.shortcut_getdef_e = QShortcut(QKeySequence('Ctrl+Shift+D'), self)
        self.shortcut_getdef_e.activated.connect(
            lambda: self.lookupSelected(
                no_lemma=True,
                trigger=LookupTrigger.shortcut_exact))
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.lookupSelected)
        self.shortcut_paste = QShortcut(QKeySequence('Ctrl+V'), self)
        self.shortcut_paste.activated.connect(self.read_button.animateClick)
        self.shortcut_web = QShortcut(QKeySequence('Ctrl+1'), self)
        self.shortcut_web.activated.connect(self.web_button.animateClick)
        self.shortcut_clearimage = QShortcut(QKeySequence('Ctrl+W'), self)
        self.shortcut_clearimage.activated.connect(lambda: self.setImage(None))
        self.shortcut_clearaudio = QShortcut(QKeySequence('Ctrl+Shift+X'), self)
        self.shortcut_clearaudio.activated.connect(self.audio_selector.discard_audio_button.animateClick)

    def onWebButton(self) -> None:
        """Shows definitions of self.word.text() in wiktionoary in browser"""

        url = settings.value("custom_url",
                             "https://en.wiktionary.org/wiki/@@@@").replace("@@@@", self.word.text())
        QDesktopServices.openUrl(QUrl(url))

    def onReaderOpen(self) -> None:
        """Opens reader in browser"""
        url = f"http://{settings.value('reader_host', '127.0.0.1', type=str)}:{settings.value('reader_port', '39285', type=str)}"
        books_dir = settings.value("books_dir")
        if not books_dir:
            QMessageBox.warning(
                self,
                "No books directory set",
                "You have not set the directory containing your books. Please set it by selecting Reader -> Set book path")
        elif not os.path.exists(books_dir):
            QMessageBox.warning(
                self,
                "Books directory does not exist",
                f"The directory ({books_dir}) containing your books is not found. Please create it or set another one.")
        else:
            QDesktopServices.openUrl(QUrl(url))

    def lookupHovered(self, target, no_lemma=False) -> None:
        if not self.shift_pressed:
            return
        self.lookup(target, no_lemma, trigger=LookupTrigger.hovered)

    @pyqtSlot()
    def lookupSelected(self, no_lemma=False, trigger=LookupTrigger.shortcut_normal) -> None:
        target = self.getCurrentWord()
        if target:  # If word not empty
            self.lookup(target, no_lemma, trigger)

    def getCurrentWord(self) -> str:
        """Returns currently selected word. If there isn't any, last selected word is returned"""

        selected = ""
        for text_field in [self.sentence, self.definition, self.definition2]:
            if text_field.hasFocus():
                cursor = text_field.textCursor()
                if selected := cursor.selectedText():
                    logger.debug(f"Manually selected text: {selected} from text field {text_field}")
                    break

        if not selected and self.sentence.hasFocus():
            cursor_position = self.sentence.textCursor().position()

            cursor.movePosition(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
            word_start_position = cursor.position()

            cursor.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
            word_end_position = cursor.position()

            if word_start_position != word_end_position and (
                    word_start_position <= cursor_position <= word_end_position):
                selected = self.sentence.toPlainText()[word_start_position:word_end_position].replace('_', '')
                logger.debug(f"Automatic selection of touched word: {selected}")
            else:
                logger.debug("Attempted automatic selection but cursor isn't touching any word")

        word_field_content = ""
        if self.word.hasFocus():
            logger.debug(f"Word field has focus, using its text: {self.word.text()}")
            word_field_content = self.word.text()

        hovered = ""
        # If the word under cursor is different from the previous one, we consider it
        if self.previous_word != self.sentence.word_under_cursor.strip():
            hovered = self.sentence.word_under_cursor.strip()
            logger.debug(f"Using hovered word: {hovered}")
        target = str.strip(selected
                           or word_field_content
                           or hovered
                           or self.previous_word
                           or "")
        logger.debug("Current word: " + target)

        return target

    def findDuplicates(self, word: str, sentence: str) -> list[int]:
        """Check for duplicates of note in Anki
        We support using either sentence or word as first field
        word is already lemmatized
        Returns note ids if card with word found in Anki, None if not found"""
        if self.checkAnkiConnect() == 0:
            return []
        api = settings.value("anki_api", "http://127.0.0.1:8765")

        note_type = settings.value("note_type")
        logger.debug(f'Trying to obtain fields for note type "{note_type}"')

        fields = modelFieldNames(api, note_type)
        logger.debug(f'Fields for note type "{note_type}": {fields}')
        if not fields:
            logger.error(f"Could not obtain fields for note type {note_type}")
            self.note_type_first_field = ""
            return []
        if fields[0] == settings.value("word_field"):
            logger.info(
                f'First field is word field, trying to find a note with field "{fields[0]}" having value "{word}"')
            find_query = f"\"{fields[0]}:{word}\""
            self.note_type_first_field = "word"
        elif fields[0] == settings.value("sentence_field"):
            logger.info(
                f'First field is sentence field, trying to find a note with field "{fields[0]}" having value "{sentence}"')
            find_query = f"\"{fields[0]}:{sentence}\""
            self.note_type_first_field = "sentence"
        else:
            logger.error(f"First field is neither word field nor sentence field, skipping checking for duplicates")
            return []
        try:
            notes_found = findNotes(api, find_query)

            if notes_found:
                logger.debug(f"Found notes for \"{word}\": {notes_found}")
                return cast(list[int], notes_found)
            else:
                logger.debug("Did not find Anki note")
                return []
        except Exception:
            logger.debug("Did not find Anki note with query: " + find_query)
            return []

    def lookup(self, target: str, no_lemma=False, trigger=LookupTrigger.double_clicked) -> None:
        target = target.strip()
        target = remove_punctuations(target)
        # refuse to look up if the word is empty
        if not target:
            return
        # Refuse to look up if word is the same as previous AND trigger is the same as previous
        if target == self.previous_word and trigger == self.previous_trigger:
            logger.debug("Same word and trigger as previous, skipping look up")
            return
        if settings.value("bold_word", True, type=bool):
            self.boldWordInSentence(target)
        langcode = settings.value("target_language", "en")
        lemma = lem_word(target, langcode)
        self.rec.recordLookup(
            LookupRecord(
                word=target,
                language=self.getLanguage(),
                source="vocabsieve"
            )
        )
        if self.known_data:
            word_record = self.known_data.get(
                lemma,
                WordRecord(lemma=lemma, language=langcode)
            )
            threshold = settings.value(
                "tracking/known_threshold",
                100,
                type=int) if lemma not in self.cognates else settings.value(
                "tracking/known_threshold_cognate",
                25,
                type=int)
            modifier = self.rec.getModifier(langcode, lemma)
            self.word_record_display.setWordRecord(word_record, self.getWordActionWeights(), threshold, modifier)

        rules = json.loads(settings.value("word_regex", "[]"))

        self.definition.lookup(target, no_lemma, rules)
        if settings.value("sg2_enabled", False, type=bool):
            self.definition2.lookup(target, no_lemma, rules)

        self.freq_widget.lookup(target, True, settings.value("freq_display", "Stars"))
        self.audio_selector.lookup(target)

        self.previous_word = target
        self.previous_trigger = trigger

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
        filename = str(int(time.time() * 1000)) + '.' + settings.value("img_format", "jpg")
        logger.debug(f"Received image, saving to disk as {filename}")
        self.image_path = os.path.join(datapath, "images", filename)
        content.save(
            self.image_path, quality=settings.value("img_quality", -1, type=int)
        )
        self.image_viewer.setPixmap(content)

    def getConvertToUppercase(self) -> bool:
        return bool(settings.value("capitalize_first_letter", False, type=bool))

    def clipboardChanged(self, even_when_focused=False, selection=False):
        """
        If the input is just a single word, we look it up right away.
        If it's a json and has the required fields, we use these fields to
        populate the relevant fields.
        Otherwise we dump everything to the Sentence field.
        By default this is not activated when the window is in focus to prevent
        mistakes, unless it is used from the button.
        """
        if selection:
            text = QApplication.clipboard().text(QClipboard.Selection)  # type: ignore
            # Ignore if empty, which happens when window loses focus
            if not text.strip():
                return
        else:
            # I am not sure how you can copy an image to PRIMARY
            # so here we go
            if QApplication.clipboard().mimeData().hasImage():
                self.setImage(QApplication.clipboard().pixmap())
                return

            text = QApplication.clipboard().text()

        should_convert_to_uppercase = self.getConvertToUppercase()
        lang = settings.value("target_language", "en")
        # Check if any of the text box widgets are focused
        # If they are, ignore the clipboard change
        is_focused = (time.time() - self.last_got_focus > 0.2)\
            and (self.sentence.hasFocus()
                 or self.word.hasFocus()
                 or self.definition.hasFocus()
                 or self.definition2.hasFocus())\
            or self.hasFocus()
        # Allow pasting right after focus for wayland users
        # because wayland doesn't allow pasting from inactive windows

        if is_focused and not even_when_focused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            target = re.sub('[\\?\\.!«»…()\\[\\]]*', "", target)
            sentence = preprocess_clipboard(copyobj['sentence'], lang, should_convert_to_uppercase)
            self.setSentence(sentence)
            self.setWord(target)
            self.lookup(target)
        elif self.single_word.isChecked() and is_oneword(preprocess_clipboard(text, lang, should_convert_to_uppercase)):
            self.setSentence(word := preprocess_clipboard(text, lang, should_convert_to_uppercase))
            self.setWord(word)
            self.lookup(text)
        else:
            self.setSentence(preprocess_clipboard(text, lang, should_convert_to_uppercase))

    def discard_current_audio(self):
        self.audio_selector.clear()

    def boldWordInSentence(self, word: str) -> None:
        self.sentence.unbold()
        sentence_text = self.sentence.toPlainText()
        # Add bold underscores around for each word with the same lemma
        lemma = lem_word(word, self.getLanguage())
        already_bolded = set()
        for token in sentence_text.split():
            token = re.sub('[\\?\\.!«»…()\\[\\]]*', "", token)
            if lem_word(token, self.getLanguage()) == lemma and token not in already_bolded:
                self.sentence.bold(token)
                already_bolded.add(token)

    def getLanguage(self) -> str:
        return settings.value("target_language", "en")  # type: ignore

    def getLemGreedy(self) -> bool:
        return settings.value("lem_greedily", False, type=bool)  # type: ignore

    def createNote(self) -> None:
        if self.checkAnkiConnect() == 0:
            return

        allow_duplicates = False
        sentence = self.sentence.toAnki()
        if note_ids := self.findDuplicates(self.word.text(), sentence):
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(
                f'Note(s) with {self.note_type_first_field} "{self.word.text() if self.note_type_first_field == "word" else sentence}" already exists in your Anki database.\n' +
                f"Do you still want to add the note?\n" +
                "\n".join(
                    f"Note id: {id}, created {unix_milliseconds_to_datetime_str(id)}" for id in note_ids))
            msgBox.setWindowTitle("Note already exists")
            msgBox.addButton("Add anyway", QMessageBox.AcceptRole)
            msgBox.addButton("Cancel", QMessageBox.RejectRole)
            msgBox.addButton("Fail existing", QMessageBox.DestructiveRole)
            msgBox.addButton("View note(s)", QMessageBox.HelpRole)
            msgBox.exec()
            result = msgBox.buttonRole(msgBox.clickedButton())
            if result == QMessageBox.RejectRole:
                logger.info("User cancelled adding duplicate note")
                return
            elif result == QMessageBox.HelpRole:
                logger.info("User pressed view while adding duplicate note")
                self.guiBrowseNotes(note_ids)
                return
            elif result == QMessageBox.AcceptRole:
                logger.info("User decided to add duplicate note")
                allow_duplicates = True
            elif result == QMessageBox.DestructiveRole:
                logger.info("User decided to fail existing note")
                failCards(settings.value("anki_api"), note_ids)
                return

        anki_settings = self.getAnkiSettings()

        logger.info("Creating note")

        note = SRSNote(
            word=self.word.text(),
            sentence=sentence,
            definition1=self.definition.toAnki(),
            definition2=self.definition2.toAnki(),
            audio_path=self.audio_selector.current_audio_path,
            image=self.image_path,
            tags=settings.value("tags", "vocabsieve").strip().split() + self.tags.text().strip().split()
        )

        content = prepareAnkiNoteDict(anki_settings, note)
        logger.debug("Prepared Anki note json" + json.dumps(content, indent=4, ensure_ascii=False))
        try:
            self.last_added_note_id = addNote(
                settings.value("anki_api", "http://127.0.0.1:8765"),
                content,
                allow_duplicates
            )
            self.rec.recordNote(note, json.dumps(content, indent=4, ensure_ascii=False))
            self.status("Added note to Anki")
            # Clear fields
            self.setImage(None)
            self.sentence.setText("")
            self.word.setText("")
            self.definition.reset()
            self.definition2.reset()
            self.audio_selector.clear()
            self.previous_word = ""
            logger.info("Note added to Anki")
        except Exception as e:
            logger.error("Failed to add note to Anki: " + repr(e))
            return

    def viewLastNote(self) -> None:
        self.guiBrowseNote(self.last_added_note_id)

    def guiBrowseNote(self, note_id: int) -> None:
        """Visualize the card of the given id in the Anki Card Browser"""
        if note_id == -1:
            return

        if self.checkAnkiConnect() == 0:
            return

        logger.info(f"Opening Anki Card Browser and looking up id {note_id}")

        gui_query = f"nid:{note_id}"
        try:
            guiBrowse(
                settings.value("anki_api", "http://127.0.0.1:8765"),
                gui_query
            )
        except Exception as e:  # This shouldn't really be possible
            logger.error(f"Unable to guiBrowse for \"{note_id}\": " + repr(e))
            return

    def guiBrowseNotes(self, note_ids: list[int]) -> None:
        """Visualize the card of the given id in the Anki Card Browser"""
        if not note_ids:
            return

        if self.checkAnkiConnect() == 0:
            return

        logger.info(f"Opening Anki Card Browser and looking up id {note_ids}")

        gui_query = f"nid:{','.join(str(id) for id in note_ids)}"
        try:
            guiBrowse(
                settings.value("anki_api", "http://127.0.0.1:8765"),
                gui_query
            )
        except Exception as e:  # This shouldn't really be possible
            logger.error(f"Unable to guiBrowse for \"{note_ids}\": " + repr(e))
            return

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

    def initTimers(self) -> None:
        logger.debug("Initializing timers")
        #self.showStats()
        #_timer = QTimer()
        #_timer.timeout.connect(self.showStats)
        #_timer.start(2000)
        timer_known_data = QTimer(self)
        refresh_every = settings.value("tracking/known_data_lifetime", 1800, type=int) * 1000 // 10
        # Attempt to refresh every 30s, but refresh will only happen if data is expired
        timer_known_data.setInterval(refresh_every)
        timer_known_data.timeout.connect(self.getKnownDataOnThread)
        timer_known_data.start()
        self.getKnownDataOnThread()

    def showStats(self) -> None:
        lookups = self.rec.countLookupsToday()
        notes = self.rec.countNotesToday()
        self.stats_label.setText(f"L:{str(lookups)} N:{str(notes)}")

    def time(self) -> str:
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def status(self, msg: str) -> None:
        self.status_bar.showMessage(self.time() + " " + msg)

    def warn(self, text: str) -> None:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(text)
        msg.exec()

    def startServer(self) -> None:
        if settings.value("reader_enabled", True, type=bool):
            self.thread2 = QThread()
            port = settings.value("reader_port", 39285, type=int)
            host = settings.value("reader_host", "127.0.0.1")
            self.worker2 = ReaderServer(self, host, port)
            self.worker2.moveToThread(self.thread2)
            self.thread2.started.connect(self.worker2.start_api)
            self.thread2.start()


def main():
    # In Windows 11 QToolTip background color is not displayed correctly in dark theme.
    # To get the theme to work properly on Windows 11, add an additional qss that removes the border.
    # For whatever reason, this works and allows QT to render the tool boxes correctly.
    # See https://github.com/5yutan5/PyQtDarkTheme/issues/239 for more info.
    qss = "QToolTip { border: 0px; }" if sys.platform == "win32" else ""

    if (theme := settings.value("theme", 'auto')) and theme != "system":
        if color := settings.value("accent_color"):
            qdarktheme.setup_theme(theme, custom_colors={"primary": color}, additional_qss=qss)
        else:
            qdarktheme.setup_theme(theme, additional_qss=qss)
   # if using system, don't set up theme

    w = MainWindow()

    w.show()
    w.audio_selector.alignDiscardButton()  # fix annoying issue of misalignment
    app.exec()
    if not w.is_wayland:
        w.monitor.stop_monitoring()
