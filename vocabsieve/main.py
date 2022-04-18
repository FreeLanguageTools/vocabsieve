import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qt import QDesktopServices, QUrl
from os import path
import os
import functools
import platform
import json
from collections import deque
import re
DEBUGGING = None
if os.environ.get("VOCABSIEVE_DEBUG"):
    DEBUGGING = True
    QCoreApplication.setApplicationName("VocabSieve" + os.environ.get("VOCABSIEVE_DEBUG"))
else:
    QCoreApplication.setApplicationName("VocabSieve")
QCoreApplication.setOrganizationName("FreeLanguageTools")
from .config import *
from .tools import *
from .db import *
from .dictionary import *
from .api import LanguageServer
from . import __version__
from .ext.reader import ReaderServer
from .ext.importer import KindleImporter

# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text
if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"

@functools.lru_cache()
class GlobalObject(QObject):
    """
    We need this to enable the textedit widget to communicate with the main window
    """
    def __init__(self):
        super().__init__()
        self._events = {}

    def addEventListener(self, name, func):
        if name not in self._events:
            self._events[name] = [func]
        else:
            self._events[name].append(func)

    def dispatchEvent(self, name):
        functions = self._events.get(name, [])
        for func in functions:
            QTimer.singleShot(0, func)




class DictionaryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VocabSieve")
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget = QWidget()
        self.settings = QSettings()
        self.rec = Record()
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.audio_path = ""
        self.scaleFont()
        self.initWidgets()
        if self.settings.value("orientation", "Vertical") == "Vertical":
            self.resize(400, 700)
            self.setupWidgetsV()
        else:
            self.resize(1000, 300)
            self.setupWidgetsH()
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.initTimer()
        self.updateAnkiButtonState()
        self.setupShortcuts()
        self.prev_states = deque(maxlen=30)

        GlobalObject().addEventListener("double clicked", self.lookupClicked)
        if self.settings.value("primary", False, type=bool)\
            and QClipboard.supportsSelection(QApplication.clipboard()):
            QApplication.clipboard().selectionChanged.connect(lambda: self.clipboardChanged(False, True))
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

    def scaleFont(self):
        font = QApplication.font()
        font.setPointSize(int(font.pointSize() * self.settings.value("text_scale", type=int)/100))
        self.setFont(font)

    def focusInEvent(self, event):
        if platform.system() == "Darwin":
            self.clipboardChanged(evenWhenFocused=True)
        super().focusInEvent(event)

    def initWidgets(self):
        self.namelabel = QLabel("<h2 style=\"font-weight: normal;\">VocabSieve v" + __version__ + "</h2>")
        self.menu = QMenuBar(self)
        self.sentence = MyTextEdit()
        self.sentence.setPlaceholderText("Sentence copied to the clipboard will show up here.")
        self.sentence.setMinimumHeight(50)
        self.sentence.setMaximumHeight(300)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Word will appear here when looked up.")
        self.definition = MyTextEdit()
        self.definition.setMinimumHeight(70)
        self.definition.setMaximumHeight(1800)
        self.definition2 = MyTextEdit()
        self.definition2.setMinimumHeight(70)
        self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("Type in a list of tags to be used, separated by spaces (same as in Anki).")
        self.sentence.setToolTip("You can look up any word in this box by double clicking it, or alternatively by selecting it, then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton("Define (Direct)")
        self.lookup_exact_button.setToolTip("This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}-S]")

        self.undo_button = QPushButton("Undo")
        self.config_button = QPushButton("Configure..")
        self.read_button = QPushButton("Read clipboard")
        self.bar = QStatusBar()
        self.setStatusBar(self.bar)
        self.stats_label = QLabel()

        self.single_word = QCheckBox("Single word lookups")
        self.single_word.setToolTip("If enabled, vocabsieve will act as a quick dictionary and look up any single words copied to the clipboard.\n"\
            "This can potentially send your clipboard contents over the network if an online dictionary service is used.\n"\
            "This is INSECURE if you use password managers that copy passwords to the clipboard.")

        self.web_button = QPushButton("Open webpage")
        self.freq_display = QLCDNumber()
        self.freq_display.setSegmentStyle(QLCDNumber.Flat)
        self.freq_display.display(0)

        self.audio_selector = QListWidget()
        self.audio_selector.setMinimumHeight(50)
        self.audio_selector.setFlow(QListView.TopToBottom)
        self.audio_selector.setResizeMode(QListView.Adjust)
        self.audio_selector.setWrapping(True)

        self.audio_selector.currentItemChanged.connect(lambda x: (
            self.play_audio(x.text()[2:]) if x != None else None
            ))

        self.definition.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))
        self.definition2.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))
        self.definition.setPlaceholderText('You can look up any word in the "Sentence" box by double clicking it, or alternatively by selecting it, then press "Get definition".')


    def play_audio(self, x):
        QCoreApplication.processEvents()
        if x != None:
            self.audio_path = play_audio(x, self.audios, self.settings.value("target_language", "en"))

         

    def setupWidgetsV(self):
        self.layout = QGridLayout(self.widget)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 2)

        self.layout.addWidget(self.single_word, 1, 0, 1, 3)

        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 2, 0)
        self.layout.addWidget(self.undo_button, 2, 1)
        self.layout.addWidget(self.read_button, 2, 2)

        self.layout.addWidget(self.sentence, 3, 0, 1, 3)
        self.layout.setRowStretch(3, 1)
        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 4, 0)

        if self.settings.value("lemmatization", True, type=bool):
            self.layout.addWidget(self.lookup_button, 4, 1)
            self.layout.addWidget(self.lookup_exact_button, 4, 2)
        else:
            self.layout.addWidget(self.lookup_button, 4, 1, 1, 2)
        
        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 6, 0)
        self.layout.addWidget(self.freq_display, 6, 1)
        self.layout.addWidget(self.web_button, 6, 2)
        self.layout.addWidget(self.word, 5, 0, 1, 3)
        if self.settings.value("dict_source2", "<disabled>") != "<disabled>":
            self.layout.addWidget(self.definition, 7, 0, 2, 3)
            self.layout.setRowStretch(7, 2)
            self.layout.addWidget(self.definition2, 9, 0, 2, 3)
            self.layout.setRowStretch(9, 2)
        else:
            self.layout.addWidget(self.definition, 7, 0, 4, 3)
            self.layout.setRowStretch(7, 2)

        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Pronunciation</h3>"), 11, 0, 1, 3)
        self.layout.addWidget(self.audio_selector, 12, 0, 1, 3)
        self.layout.setRowStretch(12, 1)
        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Additional tags</h3>"), 13, 0, 1, 3)

        self.layout.addWidget(self.tags, 14, 0, 1, 3)

        self.layout.addWidget(self.toanki_button, 15, 0, 1, 3)
        self.layout.addWidget(self.config_button, 16, 0, 1, 3)

    def setupButtons(self):
        self.lookup_button.clicked.connect(lambda: self.lookupClicked(True))
        self.lookup_exact_button.clicked.connect(lambda: self.lookupClicked(False))

        self.web_button.clicked.connect(self.onWebButton)

        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(True))

        self.sentence.textChanged.connect(self.updateAnkiButtonState)
        self.undo_button.clicked.connect(self.undo)

        self.bar.addPermanentWidget(self.stats_label)

    def setupMenu(self):
        self.open_reader_action = QAction("&Reader")
        self.menu.addAction(self.open_reader_action)
        if not self.settings.value("reader_enabled", True, type=bool):
            self.open_reader_action.setEnabled(False)
        importmenu = self.menu.addMenu("&Import")
        helpmenu = self.menu.addMenu("&Help")
        self.help_action = QAction("&Help")
        self.about_action = QAction("&About")
        helpmenu.addAction(self.help_action)
        helpmenu.addAction(self.about_action)
    
        self.import_koreader_action = QAction("Import K&OReader")
        self.import_koreader_action.setEnabled(False)
        self.import_kindle_action = QAction("Import &Kindle")

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.import_kindle_action.triggered.connect(self.importkindle)
        
        
        importmenu.addActions([self.import_koreader_action, self.import_kindle_action])

        self.setMenuBar(self.menu)

    def onHelp(self):
        url = f"https://freelanguagetools.org/2021/07/simple-sentence-mining-ssmtool-full-tutorial/"
        QDesktopServices.openUrl(QUrl(url))

    def onAbout(self):
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()


    def setupWidgetsH(self):
        self.layout = QGridLayout(self.widget)
        #self.sentence.setMaximumHeight(99999)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 3)
        self.layout.addWidget(self.single_word, 0, 3, 1, 2)
        self.layout.setColumnStretch(0, 5)
        self.layout.setColumnStretch(1, 5)
        self.layout.setColumnStretch(2, 5)
        self.layout.setColumnStretch(3, 5)
        self.layout.setColumnStretch(4, 5)

        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 1, 0)
        self.layout.addWidget(self.freq_display, 1, 1)
        self.layout.addWidget(self.undo_button, 6, 0)
        self.layout.addWidget(self.read_button, 6, 1)

        self.layout.addWidget(self.sentence, 2, 0, 3, 2)
        self.layout.addWidget(self.audio_selector, 5, 0, 1, 2)
        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 1, 2)

        self.layout.addWidget(self.lookup_button, 3, 2)
        self.layout.addWidget(self.lookup_exact_button, 4, 2)
        
        self.layout.addWidget(QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 1, 3)
        self.layout.addWidget(self.web_button, 1, 4)
        self.layout.addWidget(self.word, 2, 2, 1, 1)
        if self.settings.value("dict_source2", "<disabled>") != "<disabled>":
            self.layout.addWidget(self.definition, 2, 3, 2, 2)
            self.layout.addWidget(self.definition2, 4, 3, 2, 2)
        else:
            self.layout.addWidget(self.definition, 2, 3, 4, 2)

        
        self.layout.addWidget(QLabel("Additional tags"), 5, 2, 1, 1)

        self.layout.addWidget(self.tags, 6, 2)

        self.layout.addWidget(self.toanki_button, 6, 3, 1, 1)
        self.layout.addWidget(self.config_button, 6, 4, 1, 1)
   
    def updateAnkiButtonState(self, forceDisable=False):
        if self.sentence.toPlainText() == "" or forceDisable:
            self.toanki_button.setEnabled(False)
        else:
            self.toanki_button.setEnabled(True)

    def configure(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec()

    def importkindle(self):
        #fdialog = QFileDialog()
        #fdialog.setFileMode(QFileDialog.ExistingFile)
        #fdialog.setAcceptMode(QFileDialog.AcceptOpen)
        #fdialog.setNameFilter("Kindle clippings files (*.txt)")
        #fdialog.exec()
        fname = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            filter='Kindle clippings files (*.txt)',
            )[0]
        if not fname:
            return
        else:
            self.import_kindle = KindleImporter(self, fname)
            self.import_kindle.exec()

    def setupShortcuts(self):
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.toanki_button.animateClick)
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.lookup_button.animateClick)

    def getCurrentWord(self):
        cursor = self.sentence.textCursor()
        selected = cursor.selectedText()
        cursor2 = self.definition.textCursor()
        selected2 = cursor2.selectedText()
        target = str.strip(selected or selected2
                                    or self.previousWord
                                    or self.word.text()
                                    or "")
        self.previousWord = target

        return target

    def onWebButton(self):
        url = self.settings.value("custom_url").replace("@@@@", self.word.text())
        QDesktopServices.openUrl(QUrl(url))

    def onReaderOpen(self):
        url = f"http://{self.settings.value('reader_host', '127.0.0.1', type=str)}:{self.settings.value('reader_port', '39285', type=str)}"
        QDesktopServices.openUrl(QUrl(url))

    def lookupClicked(self, use_lemmatize=True):
        target = self.getCurrentWord()
        self.updateAnkiButtonState()
        if target == "":
            return
        self.lookupSet(target, use_lemmatize)


    def setState(self, state):
        self.word.setText(state['word'])
        self.definition.setText(state['definition'].strip())
        if state.get('definition2') != None:
            self.definition2.setText(state['definition2'].strip())
        cursor = self.sentence.textCursor()
        cursor.clearSelection()
        self.sentence.setTextCursor(cursor)

    def getState(self):
        return {'word': self.word.text(), 'definition': self.definition.toPlainText().replace("\n", "<br>")}

    def undo(self):
        try:
            self.setState(self.prev_states.pop())
        except IndexError:
            self.setState({'word': "", 'definition': ""})

    def setSentence(self, content):
        self.sentence.setText(str.strip(content))

    def setWord(self, content):
        self.word.setText(content)

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
            text = QApplication.clipboard().text()
        remove_spaces = self.settings.value("remove_spaces")
        lang = self.settings.value("target_language", "en")
        if self.isActiveWindow() and not evenWhenFocused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            target = re.sub('[\?\.!«»…()\[\]]*', "", target)
            self.previousWord = target
            sentence = preprocess_clipboard(copyobj['sentence'], lang)
            self.setSentence(sentence)
            self.setWord(target)
            self.lookupSet(target)
        elif self.single_word.isChecked() and is_oneword(preprocess_clipboard(text, lang)):
            self.setSentence(word:=preprocess_clipboard(text, lang))
            self.setWord(word)
            self.lookupSet(text)
        else:
            self.setSentence(preprocess_clipboard(text, lang))

    def lookupSet(self, word, use_lemmatize=True):
        sentence_text = self.sentence.toPlainText()
        if self.settings.value("bold_word", type=bool) == True:
            sentence_text = sentence_text.replace("_","").replace(word, f"__{word}__")
        self.sentence.setText(sentence_text)
        QCoreApplication.processEvents()
        result = self.lookup(word, use_lemmatize)
        self.setState(result)
        QCoreApplication.processEvents()
        self.audio_path = None
        if self.settings.value("audio_dict", "<disabled>") != "<disabled>":
            try:
                self.audios = getAudio(
                    word, self.settings.value("target_language"), 
                    dictionary=self.settings.value("audio_dict"),
                    custom_dicts=json.loads(self.settings.value("custom_dicts"))
                    )
            except Exception:
                self.audios = {}
            self.audio_selector.clear()
            if len(self.audios) > 0:
                for item in self.audios:
                    self.audio_selector.addItem("🔊 " + item)
                self.audio_selector.setCurrentItem(
                    self.audio_selector.item(0)
                    )
                #self.play_audio(list(self.audios.keys())[0])

    def lookup(self, word, use_lemmatize=True, record=True):
        """
        Look up a word and return a dict with the lemmatized form (if enabled)
        and definition
        """
        TL = self.settings.value("target_language", "en")
        self.prev_states.append(self.getState())
        lemmatize = use_lemmatize and self.settings.value("lemmatization", True, type=bool)
        lemfreq = self.settings.value("lemfreq", True, type=bool)
        short_sign = "Y" if lemmatize else "N"
        language = TL #This is in two letter code
        gtrans_lang = self.settings.value("gtrans_lang", "en")
        dictname = self.settings.value("dict_source", "Wiktionary (English)")
        freqname = self.settings.value("freq_source", "<disabled>")
        word = re.sub('[«»…,()\[\]_]*', "", word)
        if freqname != "<disabled>":
            try:
                freq = getFreq(word, language, lemfreq, freqname)
            except TypeError:
                freq = -1
            self.freq_display.display(freq)
        if record:
            self.status(f"L: '{word}' in '{language}', lemma: {short_sign}, from {dictionaries.get(dictname, dictname)}")
        try:
            item = lookupin(word, language, lemmatize, dictname, gtrans_lang, self.settings.value("gtrans_api"))
            if record:
                self.rec.recordLookup(word, item['definition'], TL, lemmatize, dictionaries.get(dictname, dictname), True)
        except Exception as e:
            if record:
                self.status(str(e))
                self.rec.recordLookup(word, None, TL, lemmatize, dictionaries.get(dictname, dictname), False)
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
            item2 = lookupin(word, language, lemmatize, dict2name, gtrans_lang)
            if record:
                self.rec.recordLookup(word, item['definition'], TL, lemmatize, dictionaries.get(dict2name, dict2name), True)
        except Exception as e:
            self.status("Dict-2 failed" + str(e))
            if record:
                self.rec.recordLookup(word, None, TL, lemmatize, dictionaries.get(dict2name, dict2name), False)
            self.definition2.clear()
            return item
        return {"word": item['word'], 'definition': item['definition'], 'definition2': item2['definition']}
        
    def createNote(self):
        sentence = self.sentence.toPlainText().replace("\n", "<br>")
        if self.settings.value("bold_word", type=bool) == True:
            sentence = re.sub(r"__([ \w]+)__", r"<strong>\1</strong>", sentence)
        if self.settings.value("remove_spaces", type=bool) == True:
            sentence = re.sub("\s", "", sentence)
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
        definition = self.definition.toPlainText().replace("\n", "<br>")
        content['fields'][self.settings.value('definition_field')] = definition
        if self.settings.value("dict_source2", "<disabled>") != '<disabled>':
            try:
                definition2 = self.definition2.toPlainText().replace("\n", "<br>")
                if self.settings.value("definition2_field", "<disabled>") == "<disabled>":
                    self.warn("Aborted.\nYou must have field for Definition#2 in order to use two dictionaries.")
                    return
                content['fields'][self.settings.value('definition2_field')] = definition2
            except Exception as e:
                return

        if self.settings.value("pronunciation_field", "<disabled>") != '<disabled>' and self.audio_path:
            content['audio'] = {
                "path": self.audio_path,
                "filename": path.basename(self.audio_path),
                "fields": [
                    self.settings.value("pronunciation_field")
                ]
            }

        self.status("Adding note")
        api = self.settings.value("anki_api")
        try:
            addNote(api, content)
            self.rec.recordNote(str(content), True)
            self.sentence.clear()
            self.word.clear()
            self.definition.clear()
            self.definition2.clear()
            self.status(f"Note added: '{word}'")
        except Exception as e:
            self.rec.recordNote(str(content), False)
            self.status(f"Failed to add note: {word}")
            self.errorNoConnection(e)
            return

    def errorNoConnection(self, error):
        """
        Dialog window sent when something goes wrong in configuration step
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(str(error)
            + "\n\nHints:"
            + "\nAnkiConnect must be running in order to add notes."
            + "\nIf you have AnkiConnect running at an alternative endpoint,"
            + "\nbe sure to change it in the configuration.")
        msg.exec()

    def initTimer(self):
        self.showStats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showStats)
        self.timer.start(500)

    def showStats(self):
        lookups = self.rec.countLookupsToday()
        notes = self.rec.countNotesToday()
        self.stats_label.setText(f"L:{str(lookups)} N:{str(notes)}")

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def status(self, msg):
        self.bar.showMessage(self.time() + " " + msg, 4000)

    def warn(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.exec()

    def startServer(self):
        if self.settings.value("api_enabled", True, type=bool):
            try:
                self.thread = QThread()
                port = self.settings.value("port", 39284, type=int)
                host = self.settings.value("host", "127.0.0.1")
                self.worker = LanguageServer(self, host, port)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.start_api)
                self.worker.note_signal.connect(self.onNoteSignal)
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
    
    def onNoteSignal(self, sentence: str, word: str, definition: str, tags: list):
        self.setSentence(sentence)
        self.setWord(word)
        self.definition.setText(definition)
        self.tags.setText(" ".join(tags))
        self.createNote()

class MyTextEdit(QTextEdit):

    @pyqtSlot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        GlobalObject().dispatchEvent("double clicked")
        self.textCursor().clearSelection()

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = QLabel(
            '''
© 2022 FreeLanguageTools<br><br>
Visit <a href="https://freelanguagetools.org">FreeLanguageTools.org</a> for more info on how to use this tool.<br>
You can also talk to us on <a href="https://webchat.kde.org/#/room/#flt:midov.pl">Matrix</a>
or <a href="https://t.me/fltchat">Telegram</a> for support.<br><br>

Consult <a href="https://freelanguagetools.org/2021/08/dictionaries-and-frequency-lists-for-ssm/">this link</a> 
to find compatible dictionaries. <br><br>

VocabSieve (formerly SSM, ssmtool) is free software available to you under the terms of
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.
If you found a bug, or have enhancement ideas, please open an issue on the 
Github <a href=https://github.com/FreeLanguageTools/vocabsieve>repository</a>.<br><br>

This program is yours to keep. There is no EULA you need to agree to.
No data is sent to any server other than the configured dictionary APIs.
Statistics data are stored locally.
<br><br>
Credits: <br><a href="https://en.wiktionary.org/wiki/Wiktionary:Main_Page">Wiktionary API</a><br>
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

