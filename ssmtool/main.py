import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from os import path
import functools
import platform
import json
from collections import deque

from .config import *
from .tools import *
from .db import *
from .dictionary import *
from .api import LanguageServer
from . import __version__


# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl"
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
        self.setWindowTitle("Simple Sentence Mining")
        self.setFocusPolicy(Qt.StrongFocus)
        self.resize(400, 700)
        self.widget = QWidget()
        self.settings = QSettings("FreeLanguageTools", "SimpleSentenceMining")
        self.rec = Record()
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.initWidgets()
        self.setupWidgets()
        self.startServer()
        self.initTimer()
        self.updateAnkiButtonState()
        self.setupShortcuts()
        self.prev_states = deque(maxlen=30)

        GlobalObject().addEventListener("double clicked", self.lookupClicked)
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

    def focusInEvent(self, event):
        self.clipboardChanged(evenWhenFocused=True)
        super().focusInEvent(event)

    def initWidgets(self):
        self.namelabel = QLabel("Simple Sentence Mining v" + __version__)
        self.namelabel.setFont(QFont("Sans Serif", QApplication.font().pointSize() * 1.5))

        self.sentence = MyTextEdit()
        self.sentence.setMinimumHeight(30)
        self.sentence.setMaximumHeight(130)
        self.word = QLineEdit()
        self.definition = MyTextEdit()
        self.definition.setMinimumHeight(70)
        self.definition.setMaximumHeight(1800)
        self.definition2 = MyTextEdit()
        self.definition2.setMinimumHeight(70)
        self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.label_sentence = QLabel("Sentence")
        self.label_sentence.setToolTip("You can look up any word in this box by double clicking it, or alternatively by selecting it, then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define ({MOD}-D)")
        self.lookup_exact_button = QPushButton("Define (Direct)")
        self.lookup_exact_button.setToolTip("This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note ({MOD}-S)")

        self.undo_button = QPushButton("Undo")
        self.config_button = QPushButton("Configure..")
        self.read_button = QPushButton("Read clipboard")
        self.bar = QStatusBar()
        self.setStatusBar(self.bar)
        self.stats_label = QLabel()

        self.sentence.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))
        self.definition.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))

    def setupWidgets(self):
        self.layout = QGridLayout(self.widget)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 3)

        self.layout.addWidget(QLabel("Anything copied to clipboard will appear here."), 1, 0, 1, 3)

        self.layout.addWidget(self.label_sentence, 2, 0)
        self.layout.addWidget(self.undo_button, 2, 1)
        self.layout.addWidget(self.read_button, 2, 2)

        self.layout.addWidget(self.sentence, 3, 0, 1, 3)
        self.layout.addWidget(QLabel("Word"), 4, 0)

        if self.settings.value("lemmatization", True, type=bool):
            self.layout.addWidget(self.lookup_button, 4, 1)
            self.layout.addWidget(self.lookup_exact_button, 4, 2)
        else:
            self.layout.addWidget(self.lookup_button, 4, 1, 1, 2)
        
        self.layout.addWidget(QLabel("Definition"), 6, 0, 1, 3)
        self.layout.addWidget(self.word, 5, 0, 1, 3)
        if self.settings.value("dict_source2", "Disabled") != "Disabled":
            print(self.settings.value("dict_source2", "Disabled") != "Disabled")
            self.layout.addWidget(self.definition, 7, 0, 2, 3)
            self.layout.setRowStretch(7, 1)
            self.layout.addWidget(self.definition2, 9, 0, 2, 3)
            self.layout.setRowStretch(9, 1)
        else:
            self.layout.addWidget(self.definition, 7, 0, 4, 3)
            self.layout.setRowStretch(7, 1)
        
        self.layout.addWidget(QLabel("Additional tags"), 11, 0, 1, 3)

        self.layout.addWidget(self.tags, 12, 0, 1, 3)

        self.layout.addWidget(self.toanki_button, 13, 0, 1, 3)
        self.layout.addWidget(self.config_button, 14, 0, 1, 3)

        self.lookup_button.clicked.connect(lambda _: self.lookupClicked(True))
        self.lookup_exact_button.clicked.connect(lambda _: self.lookupClicked(False))

        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda _: self.clipboardChanged(True))

        self.sentence.textChanged.connect(self.updateAnkiButtonState)
        self.undo_button.clicked.connect(self.undo)

        self.bar.addPermanentWidget(self.stats_label)

    def updateAnkiButtonState(self, forceDisable=False):
        if self.sentence.toPlainText() == "" or forceDisable:
            self.toanki_button.setEnabled(False)
        else:
            self.toanki_button.setEnabled(True)

    def configure(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec()

    def setupShortcuts(self):
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.toanki_button.animateClick)
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.lookup_button.animateClick)

    def getCurrentWord(self):
        cursor = self.sentence.textCursor()
        selected = cursor.selectedText().lower()
        cursor2 = self.definition.textCursor()
        selected2 = cursor2.selectedText().lower()
        target = str.strip(selected or selected2
                                    or self.previousWord
                                    or self.word.text()
                                    or "")
        self.previousWord = target

        return target

    def lookupClicked(self, use_lemmatize=True):
        target = self.getCurrentWord()
        print(use_lemmatize)
        self.updateAnkiButtonState()
        if target == "":
            return
        result = self.lookup(target, use_lemmatize)
        self.setState(result)

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

    def clipboardChanged(self, evenWhenFocused=False):
        """
        If the input is just a single word, we look it up right away.
        If it's a json and has the required fields, we use these fields to
        populate the relevant fields.
        Otherwise we dump everything to the Sentence field.
        By default this is not activated when the window is in focus to prevent
        mistakes, unless it is used from the button.
        """
        text = QApplication.clipboard().text()
        if self.isActiveWindow() and not evenWhenFocused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            self.setSentence(copyobj['sentence'])
            self.setWord(target)
            result = self.lookup(target)
            self.setState(result)
        elif is_oneword(text):
            self.setSentence(text)
            self.setWord(text)
            result = self.lookup(text)
            self.setState(result)
        else:
            self.setSentence(text)

    def lookup(self, word, use_lemmatize=True):
        """
        Look up a word and return a dict with the lemmatized form (if enabled)
        and definition
        """
        TL = self.settings.value("target_language", "English") 
        self.prev_states.append(self.getState())
        lemmatize = use_lemmatize and self.settings.value("lemmatization", True, type=bool)
        short_sign = "Y" if lemmatize else "N"
        language = code[TL] #This is in two letter code
        gtrans_lang = self.settings.value("gtrans_lang", "English")
        dictname = self.settings.value("dict_source", "Wiktionary (English)")
        self.status(f"L: '{word}' in '{language}', lemma: {short_sign}, from {dictionaries.get(dictname, dictname)}")
        try:
            item = lookupin(word, language, lemmatize, dictname, gtrans_lang)
            self.rec.recordLookup(word, item['definition'], TL, lemmatize, dictionaries.get(dictname, dictname), True)
        except Exception as e:
            self.status(str(e))
            self.rec.recordLookup(word, None, TL, lemmatize, dictionaries.get(dictname, dictname), False)
            self.updateAnkiButtonState(True)
            item = {
                "word": word,
                "definition": failed_lookup(word, self.settings)
                }
            return item
        dict2name = self.settings.value("dict_source2", "Disabled")
        if dict2name == "Disabled":
            return item
        try:
            item2 = lookupin(word, language, lemmatize, dict2name, gtrans_lang)
            self.rec.recordLookup(word, item['definition'], TL, lemmatize, dictionaries.get(dict2name, dict2name), True)
        except Exception as e:
            self.status("Dict-2 failed" + str(e))
            self.rec.recordLookup(word, None, TL, lemmatize, dictionaries.get(dict2name, dict2name), False)
            self.definition2.clear()
            return item
        return {"word": item['word'], 'definition': item['definition'], 'definition2': item2['definition']}

    def createNote(self):
        sentence = self.sentence.toPlainText().replace("\n", "<br>")
        tags = (self.settings.value("tags", "ssmtool").strip() + " " + self.tags.text().strip()).split(" ")
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
        if self.settings.value("dict_source2", "Disabled") != 'Disabled':
            try:
                definition2 = self.definition2.toPlainText().replace("\n", "<br>")
                if self.settings.value("definition2_field", "Disabled") == "Disabled":
                    self.warn("Aborted.\nYou must have field for Definition#2 in order to use two dictionaries.")
                    return
                content['fields'][self.settings.value('definition2_field')] = definition2
            except Exception as e:
                return

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
        try:
            self.thread = QThread()
            port = self.settings.value("port", 39284, type=int)
            host = self.settings.value("host", "127.0.0.1")
            self.worker = LanguageServer(self, host, port)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.start_api)
            self.worker.note_signal.connect(self.onNoteSignal)
            self.thread.start()
        except Exception:
            self.status("Failed to start server")
    
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
        print("Event sent")
        self.textCursor().clearSelection()

def main():
    app = QApplication(sys.argv)
    w = DictionaryWindow()

    w.show()
    sys.exit(app.exec())
