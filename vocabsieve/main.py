import csv
from operator import ge
import threading
import importlib.metadata
import os
import sys
import time
import re
from datetime import datetime
from typing import Optional
from markdown import markdown
import requests
from packaging import version
from PyQt5.QtCore import QCoreApplication, QStandardPaths, QTimer, QDateTime, QThread, QUrl
from PyQt5.QtGui import QClipboard, QKeySequence, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QShortcut, QFileDialog
import qdarktheme
import json

from .global_names import datapath
from .text_manipulation import apply_bold_char, apply_bold_tags, bold_word_in_text
from .known_words import getKnownData, getKnownWords
from .analyzer import BookAnalyzer
from .config import SettingsDialog, getVersion
from .stats import StatisticsWindow
from .dictionary import getAudio
from .importer import KindleVocabImporter, KoreaderVocabImporter, AutoTextImporter
from .reader import ReaderServer
from .contentmanager import ContentManager
from .global_events import GlobalObject
from .tools import is_json, prepareAnkiNoteDict, preprocess_clipboard, starts_with_cyrillic, is_oneword, addNote, make_source_group
from .ui.main_window_base import MainWindowBase
from .db import LocalDictionary
from .models import AnkiSettings, DictionarySourceGroup, SRSNote



class MainWindow(MainWindowBase):
    def __init__(self) -> None:
        super().__init__()
        self.datapath = datapath
        self.dictdb = LocalDictionary(self.datapath)
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.initTimer()
        self.setupShortcuts()
        self.checkUpdates()
        self.initSources()

        GlobalObject().addEventListener("double clicked", self.lookupSelected)
        if self.settings.value("primary", False, type=bool)\
                and QClipboard.supportsSelection(QApplication.clipboard())\
                and not os.environ.get("XDG_SESSION_TYPE") == "wayland":
            QApplication.clipboard().selectionChanged.connect(
                lambda: self.clipboardChanged(False, True))
        if not os.environ.get("XDG_SESSION_TYPE") == "wayland":
            QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

        if not self.settings.value("internal/configured"):
            self.configure()
            self.settings.setValue("internal/configured", True)
    
    def initSources(self):
        sg1_src_list = json.loads(self.settings.value("sg1", '["Wiktionary (English)"]'))
        self.sg1 = make_source_group(sg1_src_list, self.dictdb)
        self.definition.setSourceGroup(self.sg1)

        if self.settings.value("sg2_enabled", False, type=bool):
            sg2_src_list = json.loads(self.settings.value("sg2", '["Google Translate"]'))
            self.sg2 = make_source_group(sg2_src_list, self.dictdb)
            self.definition2.setSourceGroup(self.sg2)
        else:
            self.sg2 = DictionarySourceGroup([])
            self.definition2.setSourceGroup(self.sg2) 

    def checkUpdates(self) -> None:
        if self.settings.value("check_updates") is None:
            answer = QMessageBox.question(
                self,
                "Check updates",
                "<h2>Would you like VocabSieve to check for updates automatically on launch?</h2>"
                "Currently, the repository and releases are hosted on GitHub's servers, "
                "which will be queried for checking updates. <br>VocabSieve cannot and "
                "<strong>will not</strong> install any updates automatically."
                "<br>You can change this option in the configuration panel at any time."
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

    def setupButtons(self) -> None:
        self.lookup_button.clicked.connect(self.lookupSelected)


        self.web_button.clicked.connect(self.onWebButton)
        self.discard_audio_button.clicked.connect(self.discard_current_audio)

        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(True))


        self.bar.addPermanentWidget(self.stats_label)

    def setupMenu(self) -> None:
        readermenu = self.menu.addMenu("&Reader")
        importmenu = self.menu.addMenu("&Import")
        recordmenu = self.menu.addMenu("&Track")
        exportmenu = self.menu.addMenu("&Export")
        analyzemenu = self.menu.addMenu("A&nalyze")
        statsmenu = self.menu.addMenu("S&tatistics")
        helpmenu = self.menu.addMenu("&Help")

        self.open_reader_action = QAction("&Reader")
        self.stats_action = QAction("S&tatistics")
        self.help_action = QAction("&Setup guide")
        self.about_action = QAction("&About")
        self.content_manager_action = QAction("Content Manager")
        self.analyze_book_action = QAction("Analyze book")
        self.export_known_words_action = QAction("Export known words to JSON")
        self.export_word_scores_action = QAction("Export word scores to JSON")

        if not self.settings.value("reader_enabled", True, type=bool):
            self.open_reader_action.setEnabled(False)

        readermenu.addAction(self.open_reader_action)
        statsmenu.addAction(self.stats_action)
        helpmenu.addAction(self.help_action)
        helpmenu.addAction(self.about_action)
        recordmenu.addAction(self.content_manager_action)
        analyzemenu.addAction(self.analyze_book_action)


        self.repeat_last_import_action = QAction("&Repeat last import")
        self.import_koreader_vocab_action = QAction("K&OReader vocab builder")
        self.import_kindle_vocab_action = QAction("K&indle lookups")
        self.import_auto_text = QAction("Auto import vocab from text")

        self.export_notes_csv_action = QAction("Export &notes to CSV")
        self.export_lookups_csv_action = QAction("Export &lookup data to CSV")

        self.content_manager_action.triggered.connect(self.onContentManager)

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.repeat_last_import_action.triggered.connect(self.repeatLastImport)
        self.import_koreader_vocab_action.triggered.connect(self.importKoreader)
        self.import_kindle_vocab_action.triggered.connect(self.importKindle)
        self.import_auto_text.triggered.connect(self.importAutoText)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)
        self.stats_action.triggered.connect(self.onStats)
        self.analyze_book_action.triggered.connect(self.onAnalyzeBook)
        self.export_known_words_action.triggered.connect(self.exportKnownWords)
        self.export_word_scores_action.triggered.connect(self.exportWordScores)

        importmenu.addActions(
            [
                self.repeat_last_import_action,
                self.import_koreader_vocab_action,
                self.import_kindle_vocab_action,
                self.import_auto_text
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

    def onAnalyzeBook(self):
        path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select book",
            filter="Ebook files (*.epub *.fb2 *.mobi *.html *.azw *.azw3 *.kfx)",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
            )[0]
        if path:
            BookAnalyzer(self, path).open()

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

        known_words, *_ = getKnownWords(self.settings, self.rec)
        if self.settings.value('target_language', 'en') in ['ru', 'uk']:
            known_words = [word for word in known_words if starts_with_cyrillic(word)]

        with open(path, 'w', encoding='utf-8') as file:
            json.dump(known_words, file, indent=4, ensure_ascii=False)

    def exportWordScores(self):
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

        score, *_ = getKnownData(self.settings, self.rec)
        score = {k:v for k,v in score.items() if not k.startswith('http') and " " not in k and not k.isnumeric()}

        with open(path, 'w', encoding='utf-8') as file:
            json.dump(score, file, indent=4, ensure_ascii=False)

    def onContentManager(self):
        ContentManager(self).exec()

    def onStats(self):
        if self.checkAnkiConnect():
            stats_window = StatisticsWindow(self)
            stats_window.open()

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
        url = f"https://wiki.freelanguagetools.org/vocabsieve_setup"
        QDesktopServices.openUrl(QUrl(url))

    def checkAnkiConnect(self) -> int:
        api = self.settings.value('anki_api', 'http://127.0.0.1:8765')
        if self.settings.value('enable_anki', True, type=bool):
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
        if self.checkAnkiConnect():
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.exec()
            self.initSources()

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
            QMessageBox.warning(self, "Something went wrong", "Error: "+repr(e))

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
            QMessageBox.warning(self, "No notes are found",
                "Check if you've picked the right directory. It should be a folder containing both all of your books and KOReader settings.")
        except Exception as e:
            QMessageBox.warning(self, "Something went wrong", "Error: "+repr(e))


    def repeatLastImport(self):
        method = self.settings.value("last_import_method")
        path = self.settings.value("last_import_path")
        if not (method and path):
            QMessageBox.warning(self, "You have not imported notes before",
                "Use any one of the other two options on the menu, and you will be able to use this one next time.")
            return
        if method == "kindle":
            KindleVocabImporter(self, path).exec()
        elif method == "koreader-vocab":
            KoreaderVocabImporter(self, path).exec()
        else:
            # Nightly users, clear it for them
            self.settings.setValue("last_import_method", "")
            self.settings.setValue("last_import_path", "")
            QMessageBox.warning(self, "You have not imported notes before",
                "Use any one of the other two options on the menu, and you will be able to use this one next time.")
 

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
        self.shortcut_clearimage = QShortcut(QKeySequence('Ctrl+I'), self)
        self.shortcut_clearimage.activated.connect(lambda: self.setImage(None))
        self.shortcut_clearaudio = QShortcut(QKeySequence('Ctrl+Shift+X'), self)
        self.shortcut_clearaudio.activated.connect(self.discard_audio_button.animateClick)

    def getCurrentWord(self) -> str:
        """Returns currently selected word. If there isn't any, last selected word is returned"""
        cursor = self.sentence.textCursor()
        selected = cursor.selectedText()
        cursor2 = self.definition.textCursor()
        selected2 = cursor2.selectedText()
        cursor3 = self.definition2.textCursor()
        selected3 = cursor3.selectedText()
        target = str.strip(selected
                           or selected2
                           or selected3
                           or self.previousWord
                           or self.word.text()
                           or "")
        self.previousWord = target

        return target

    def onWebButton(self) -> None:
        """Shows definitions of self.word.text() in wiktionoary in browser"""

        url = self.settings.value("custom_url",
            "https://en.wiktionary.org/wiki/@@@@").replace("@@@@", self.word.text())
        QDesktopServices.openUrl(QUrl(url))

    def onReaderOpen(self) -> None:
        """Opens reader in browser"""

        url = f"http://{self.settings.value('reader_host', '127.0.0.1', type=str)}:{self.settings.value('reader_port', '39285', type=str)}"
        QDesktopServices.openUrl(QUrl(url))

    def lookupSelected(self) -> None:
        target = self.getCurrentWord()
        self.lookup(target)
    
    def lookup(self, target: str) -> None:
        self.boldWordInSentence(target)
        if target:
            self.definition.lookup(target)
            if self.settings.value("sg2_enabled", False, type=bool):
                self.definition2.lookup(target)
            self.getAudio(target)
        
    def getAudio(self, target: str):
        self.audio_path = ""
        if self.settings.value("audio_dict", "Forvo (all)") != "<disabled>":
            threading.Thread(target=self.fetchAudioInBackground, args=(target,)).start()

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

    def getConvertToUppercase(self) -> bool:
        return self.settings.value("capitalize_first_letter", False, type=bool)

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
            text = QApplication.clipboard().text(QClipboard.Selection) # type: ignore
        else:
            # I am not sure how you can copy an image to PRIMARY
            # so here we go
            if QApplication.clipboard().mimeData().hasImage():
                self.setImage(QApplication.clipboard().pixmap())
                return

            text = QApplication.clipboard().text()

        should_convert_to_uppercase = self.getConvertToUppercase()
        lang = self.settings.value("target_language", "en")
        if self.isActiveWindow() and not evenWhenFocused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            target = re.sub('[\\?\\.!«»…()\\[\\]]*', "", target)
            self.previousWord = target
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

    def fetchAudioInBackground(self, word):
        try:
            audios = getAudio(
                word,
                self.settings.value("target_language", 'en'),
                dictionary=self.settings.value("audio_dict", "Forvo (all)"),
                custom_dicts=json.loads(
                    self.settings.value("custom_dicts", '[]')))

            self.audio_fetched.emit(audios)
        except Exception as e:
            self.audio_fetched.emit({})
            print("Failed to fetch audio:", repr(e))

    def discard_current_audio(self):
        self.audio_selector.clear()
        self.audio_path = ""

    def boldWordInSentence(self, word) -> None:
        sentence_text = self.sentence.unboldedText
        if self.settings.value("bold_style", type=int) != 0:
            # Bold word that was clicked on, either with "<b>{word}</b>" or
            # "__{word}__".
            if self.settings.value("bold_style", type=int) == 1:
                apply_bold = apply_bold_tags
            elif self.settings.value("bold_style", type=int) == 2:
                apply_bold = apply_bold_char
            else:
                raise ValueError("Invalid bold style")

            sentence_text = bold_word_in_text(
                word,
                sentence_text,
                apply_bold,
                self.getLanguage()
                )

        if sentence_text is not None:
            self.sentence.setHtml(sentence_text)

        QCoreApplication.processEvents()
        

    def getLanguage(self) -> str:
        return self.settings.value("target_language", "en")  # type: ignore

    def getLemGreedy(self) -> bool:
        return self.settings.value("lem_greedily", False, type=bool)  # type: ignore
    
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

    def createNote(self) -> None:
        if self.checkAnkiConnect() == 0:
            return

        anki_settings = self.getAnkiSettings()

        note = SRSNote(
            word=self.word.text(),
            sentence=self.sentence.textBoldedByTags.replace("\n", "<br>"),
            definition1=self.definition.process_defi_anki(),
            definition2=self.definition2.process_defi_anki(),
            audio_path=self.audio_path,
            image=self.image_path,
            tags=self.settings.value("tags", "vocabsieve").strip().split() + self.tags.text().strip().split()
        )
        
        content = prepareAnkiNoteDict(anki_settings, note)
        print(content)
        try: 
            addNote(
                self.settings.value("anki_api", "http://127.0.0.1:8765"),
                content
            )
            self.status("Added note to Anki")
            # Clear fields
            self.sentence.setText("")
            self.word.setText("")
            self.definition.reset()
            self.definition2.reset()
            self.discard_current_audio()
            
        except Exception as e:
            print(repr(e))
            self.warn("Encountered error in adding note\n" + repr(e))
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
                print(repr(e))
                self.status("Failed to start reader server")


def main():
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    w = MainWindow()
    if theme:=w.settings.value("theme"):
        if color:=w.settings.value("accent_color"):
            qdarktheme.setup_theme(theme, custom_colors={"primary": color})
        else:
            qdarktheme.setup_theme(theme)
    else:
        qdarktheme.setup_theme("auto")

    w.show()
    sys.exit(app.exec())
