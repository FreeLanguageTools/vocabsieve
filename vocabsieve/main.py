import csv
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

from .global_names import settings, datapath
from .text_manipulation import apply_bold_char, apply_bold_tags, bold_word_in_text
from .known_words import getKnownData, getKnownWords
from .analyzer import BookAnalyzer
from .config import SettingsDialog, getVersion
from .stats import StatisticsWindow
from .dictionary import lookupin, getAudio, getFreq, lem_word, markdown_nop
from .importer import KoreaderImporter, KindleVocabImporter, KoreaderVocabImporter, AutoTextImporter
from .reader import ReaderServer
from .contentmanager import ContentManager
from .global_events import GlobalObject
from .tools import is_json, preprocess_clipboard, process_definition, starts_with_cyrillic, is_oneword, freq_to_stars, addNote, failed_lookup
from .constants import LookUpResults, DefinitionDisplayModes
from .ui.main_window_base import MainWindowBase
from .ui.searchable_text_edit import SearchableTextEdit
from .db import dictionaries

class MainWindow(MainWindowBase):
    def __init__(self) -> None:
        super().__init__()
        self.datapath = datapath
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.initTimer()
        self.setupShortcuts()
        self.checkUpdates()

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
        self.lookup_button.clicked.connect(lambda: self.lookupSelected(True))
        self.lookup_exact_button.clicked.connect(
            lambda: self.lookupSelected(False))

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
        self.import_koreader_action = QAction("K&OReader highlights (deprecated)")
        self.import_koreader_vocab_action = QAction("K&OReader vocab builder")
        self.import_kindle_new_action = QAction("K&indle lookups")
        self.import_auto_text = QAction("Auto import vocab from text")

        self.export_notes_csv_action = QAction("Export &notes to CSV")
        self.export_lookups_csv_action = QAction("Export &lookup data to CSV")

        self.content_manager_action.triggered.connect(self.onContentManager)

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.repeat_last_import_action.triggered.connect(self.repeatLastImport)
        self.import_koreader_action.triggered.connect(self.importkoreader)
        self.import_koreader_vocab_action.triggered.connect(self.importkoreaderVocab)
        self.import_kindle_new_action.triggered.connect(self.importkindleNew)
        self.import_auto_text.triggered.connect(self.importautotext)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)
        self.stats_action.triggered.connect(self.onStats)
        self.analyze_book_action.triggered.connect(self.onAnalyzeBook)
        self.export_known_words_action.triggered.connect(self.exportKnownWords)
        self.export_word_scores_action.triggered.connect(self.exportWordScores)

        importmenu.addActions(
            [
                self.repeat_last_import_action,
                self.import_koreader_action,
                self.import_koreader_vocab_action,
                self.import_kindle_new_action,
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


    def checkAnkiConnect(self):
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
                if answer == QMessageBox.Abort:
                    return 0
        else:
            return 3

    def configure(self) -> None:
        if self.checkAnkiConnect():
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
            QMessageBox.warning(self, "Something went wrong", "Error: "+repr(e))

    def importautotext(self) -> None:
        path = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select book or text file",
            filter="Book, text files (*.epub *.fb2 *.mobi *.html *.azw *.azw3 *.kfx *.txt)",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
            )[0]
        if path:
            AutoTextImporter(self, path).exec()

    def importkoreader(self) -> None:
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select a directory containing KOReader settings and ebook files",
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
            QMessageBox.warning(self, "Something went wrong", "Error: "+repr(e))

    def importkoreaderVocab(self) -> None:
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
            elif method == "koreader-vocab":
                KoreaderVocabImporter(self, path).exec()
            else:
                # Nightly users, clear it for them
                self.settings.setValue("last_import_method", "")
                self.settings.setValue("last_import_path", "")
                QMessageBox.warning(self, "You have not imported notes before",
                    "Use any one of the other two options on the menu, and you will be able to use this one next time.")
        except Exception as e:
            print("Encountered error while repeating last import, aborting:", repr(e))

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

    def lookupSelected(self, use_lemmatize=True) -> None:
        target = self.getCurrentWord()
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
            self.lookupSet(target)
        elif self.single_word.isChecked() and is_oneword(preprocess_clipboard(text, lang, should_convert_to_uppercase)):
            self.setSentence(word := preprocess_clipboard(text, lang, should_convert_to_uppercase))
            self.setWord(word)
            self.lookupSet(text)
        else:
            self.setSentence(preprocess_clipboard(text, lang, should_convert_to_uppercase))

    def updateAudioUI(self, audios):
        self.audios = audios
        self.audio_selector.clear()
        if len(self.audios):
            for item in self.audios:
                self.audio_selector.addItem("🔊 " + item)
            self.audio_selector.setCurrentItem(self.audio_selector.item(0))

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

    def lookupSet(self, word, use_lemmatize=True) -> None:
        sentence_text = self.sentence.unboldedText
        if self.settings.value("bold_style", type=int):
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
                self.getLanguage(),
                use_lemmatize,
                self.getLemGreedy())

        if sentence_text is not None:
            self.sentence.setHtml(sentence_text)

        QCoreApplication.processEvents()
        TL = self.getLanguage()
        lemmatize = self.settings.value("lemmatization", True, type=bool)
        dict_name = self.settings.value("dict_source", "Wiktionary (English)")
        result = self.lookup(word, use_lemmatize)
        self.setState(result)
        if result.get("definition") or result.get("definition2"):
            self.rec.recordLookup(word, TL, lemmatize, "vocabsieve", True, time.time())
        past_lookups_count = self.rec.countLemmaLookups(word, self.settings.value("target_language",'en'))
        if past_lookups_count <= 1:
            self.lookup_hist_label.setText("<b>new word</b>")
        else:
            self.lookup_hist_label.setText(f"<b>{past_lookups_count-1} prev. lookups</b>")
        QCoreApplication.processEvents()
        self.audio_path = ""

        if self.settings.value("audio_dict", "Forvo (all)") != "<disabled>":
            threading.Thread(target=self.fetchAudioInBackground, args=(word,)).start()

    def getLanguage(self) -> str:
        return self.settings.value("target_language", "en")  # type: ignore

    def getLemGreedy(self) -> bool:
        return self.settings.value("lem_greedily", False, type=bool)  # type: ignore

    def lookup(self, word: str, use_lemmatize: bool) -> LookUpResults:
        """
        Look up a word and return a dict with the lemmatized form (if enabled)
        and definition
        """
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
        if dictname == "<disabled>":
            word = lem_word(word, language, lem_greedily) if lemmatize else word
            self.status("Dict disabled")
            return {
                "word": word,
                "definition": ""
            }
        try:
            item = lookupin(
                word,
                language,
                lemmatize,
                lem_greedily,
                dictname,
                gtrans_lang,
                self.settings.value("gtrans_api", "https://lingva.lunar.icu"))
        except Exception as e:
            self.status(repr(e))
            item = {
                "word": word,
                "definition": failed_lookup(word, self.settings)
            }
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
        except Exception as e:
            self.status("Dict-2 failed" + repr(e))
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
            self.setImage(None)
            self.audio_selector.clear()
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
                + f"Error: {repr(e)}"
                + "\nHints: AnkiConnect must be running to add notes."
                "<br>If you wish to only add notes to the database (and "
                "export it as CSV), click Configure and uncheck 'Enable"
                " Anki' on the Anki tab."

            )

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
