import csv
import dataclasses
from operator import ge
import importlib.metadata
import os
import sys
import time
import re
from datetime import datetime
from typing import Optional
import requests
from packaging import version
import qdarktheme
import json
import threading

from markdown import markdown
from PyQt5.QtCore import QCoreApplication, QStandardPaths, QTimer, QDateTime, QThread, QUrl, pyqtSlot, QThreadPool, pyqtSignal
from PyQt5.QtGui import QClipboard, QKeySequence, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QShortcut, QFileDialog
from .global_names import datapath

from .text_manipulation import apply_bold_char, apply_bold_tags, bold_word_in_text
from .analyzer import BookAnalyzer
from .config import SettingsDialog
from .stats import StatisticsWindow
from .dictionary import preprocess_clipboard
from .importer import KindleVocabImporter, KoreaderVocabImporter, AutoTextImporter
from .reader import ReaderServer
from .contentmanager import ContentManager
from .global_events import GlobalObject
from .tools import compute_word_score, is_json, make_audio_source_group, prepareAnkiNoteDict, starts_with_cyrillic, is_oneword, addNote, make_source_group, getVersion, make_freq_source
from .ui.main_window_base import MainWindowBase
from .models import DictionarySourceGroup, LookupRecord, SRSNote, WordRecord
from sentence_splitter import SentenceSplitter
from .lemmatizer import lem_word



class MainWindow(MainWindowBase):
    got_updates = pyqtSignal(list)
    def __init__(self) -> None:
        super().__init__()
        self.datapath = datapath
        self.thread_manager = QThreadPool()
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.setupShortcuts()
        self.checkUpdatesOnThread()
        self.initSources()
        self.known_data: Optional[dict[str, WordRecord]] = None
        #self.getKnownDataOnThread()
        self.got_updates.connect(self.gotUpdatesInfo)

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
        self.splitter = SentenceSplitter(language=self.settings.value("target_language", "en"))

        if self.settings.value("freq_source", "<disabled>") != "<disabled>":
            self.freq_widget.setSource(make_freq_source(self.settings.value("freq_source"), self.dictdb))


        if self.settings.value("sg2_enabled", False, type=bool):
            sg2_src_list = json.loads(self.settings.value("sg2", '["Google Translate"]'))
            self.sg2 = make_source_group(sg2_src_list, self.dictdb)
            self.definition2.setSourceGroup(self.sg2)
        else:
            self.sg2 = DictionarySourceGroup([])
            self.definition2.setSourceGroup(self.sg2) 

        if audio_src_list:=json.loads(self.settings.value("audio_sg", '["Forvo"]')):
            self.audio_sg = make_audio_source_group(audio_src_list, self.dictdb)
            self.audio_selector.setSourceGroup(self.audio_sg)

    @pyqtSlot()
    def checkUpdatesOnThread(self) -> None:
        print("Started checking updates")
        if self.settings.value("check_updates") is None:
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
                self.settings.setValue("check_updates", True)
            if answer == QMessageBox.No:
                self.settings.setValue("check_updates", False)
            self.settings.sync()
        if self.settings.value("check_updates", True, type=bool):
            self.thread_manager.start(self.checkUpdates)
        print("Finished checking updates")

    def checkUpdates(self) -> None:
        res = requests.get("https://api.github.com/repos/FreeLanguageTools/vocabsieve/releases")
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
        self.lookup_button.clicked.connect(self.lookupSelected)
        self.lookup_exact_button.clicked.connect(lambda: self.lookupSelected(no_lemma=True))


        self.web_button.clicked.connect(self.onWebButton)

        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(True))


        self.bar.addPermanentWidget(self.stats_label)

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
        self.config_action = QAction("&Configure")
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
        configmenu.addAction(self.config_action)
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
        self.config_action.triggered.connect(self.configure)
        self.repeat_last_import_action.triggered.connect(self.repeatLastImport)
        self.import_koreader_vocab_action.triggered.connect(self.importKoreader)
        self.import_kindle_vocab_action.triggered.connect(self.importKindle)
        self.import_auto_text.triggered.connect(self.importAutoText)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)
        self.stats_action.triggered.connect(self.onStats)
        self.analyze_book_action.triggered.connect(self.onAnalyzeBook)
        self.export_known_words_action.triggered.connect(self.exportKnownWords)
        self.export_word_scores_action.triggered.connect(self.exportWordData)

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
        
        langcode = self.settings.value('target_language', 'en')

        #known_words = self.rec.getKnownWords()
        #if self.settings.value('target_language', 'en') in ['ru', 'uk']:
        #    known_words = [word for word in known_words if starts_with_cyrillic(word)]
        known_data = self.rec.getKnownData()
        known_threshold = self.settings.value('tracking/known_threshold', 100, type=int)
        known_threshold_cognate = self.settings.value('tracking/known_threshold_cognate', 25, type=int)
        known_words: list[str] = []
        cognates: set[str] = set()
        if self.dictdb.hasCognatesData():
            known_langs = self.settings.value('tracking/known_langs', 'en').split(",")
            cognates = self.dictdb.getCognatesData(langcode, known_langs)
        
        waw = self.getWordActionWeights()
        for word, word_record in known_data.items():
            if score:=compute_word_score(word_record, waw) >= known_threshold:
                known_words.append(word)
            elif score >= known_threshold_cognate and word in cognates:
                known_words.append(word)
                
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(known_words, file, indent=4, ensure_ascii=False)

    @pyqtSlot()
    def getKnownDataOnThread(self) -> None:
        self.thread_manager.start(self.getKnownData)

    @pyqtSlot()
    def getKnownData(self) -> None:
        self.known_data = self.rec.getKnownData()

    
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

        data = self.rec.getKnownData()

        with open(path, 'w', encoding='utf-8') as file:
            json.dump([dataclasses.asdict(item) for item in data.values()], file, indent=4, ensure_ascii=False)

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
        self.shortcut_clearaudio.activated.connect(self.audio_selector.discard_audio_button.animateClick)

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

    def lookupSelected(self, no_lemma=False) -> None:
        target = self.getCurrentWord()
        self.lookup(target, no_lemma)
    
    def lookup(self, target: str, no_lemma=False) -> None:
        self.boldWordInSentence(target)
        langcode = self.settings.value("target_language", "en")
        if target:
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
                self.word_record_display.setWordRecord(word_record, self.getWordActionWeights())
            self.definition.lookup(target, no_lemma)
            if self.settings.value("sg2_enabled", False, type=bool):
                self.definition2.lookup(target, no_lemma)
            self.audio_selector.lookup(target)
            self.freq_widget.lookup(target)
        

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
        return bool(self.settings.value("capitalize_first_letter", False, type=bool))

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

    def discard_current_audio(self):
        self.audio_selector.clear()

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


    def createNote(self) -> None:
        if self.checkAnkiConnect() == 0:
            return

        anki_settings = self.getAnkiSettings()

        note = SRSNote(
            word=self.word.text(),
            sentence=self.sentence.textBoldedByTags.replace("\n", "<br>"),
            definition1=self.definition.process_defi_anki(),
            definition2=self.definition2.process_defi_anki(),
            audio_path=self.audio_selector.current_audio_path,
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
            self.audio_selector.clear()
            
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
    from .global_names import settings
    if theme:=settings.value("theme"):
        if color:=settings.value("accent_color"):
            qdarktheme.setup_theme(theme, custom_colors={"primary": color})
        else:
            qdarktheme.setup_theme(theme)
    else:
        qdarktheme.setup_theme("auto")
    w = MainWindow()

    w.show()
    w.audio_selector.alignDiscardButton() # fix annoying issue of misalignment
    sys.exit(app.exec())
