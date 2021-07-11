import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from wiktionaryparser import WiktionaryParser
from os import path
import functools
from .config import *
from .tools import *
from . import __version__

@functools.lru_cache()
class GlobalObject(QObject):
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
        self.resize(400, 500)
        self.widget = QWidget()
        self.settings = QSettings("FreeLanguageTools", "SimpleSentenceMining")
        self.initDictionary()
        self.setCentralWidget(self.widget)
        self.initWidgets()
        self.setupWidgets()
        self.setupShortcuts()

        GlobalObject().addEventListener("double clicked", self.getDefinition)
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

    def initWidgets(self):
        self.namelabel = QLabel("Simple Sentence Mining v" + __version__)
        self.namelabel.setFont(QFont("Sans Serif", QApplication.font().pointSize() * 1.5))
        self.sentence = MyTextEdit("")
        self.sentence.setMinimumHeight(30)
        self.sentence.setMaximumHeight(120)
        self.word = QLineEdit("")
        self.definition = MyTextEdit("")
        self.definition.setMinimumHeight(70)
        self.definition.setMaximumHeight(800)
        self.label_sentence = QLabel("Sentence")
        self.label_sentence.setToolTip("You can look up any word in this box by double clicking it, or alternatively by selecting it, then press \"Get definition\".")
        self.label_word = QLabel("Word")
        self.label_def = QLabel("Definition")
        self.lookup_button = QPushButton("Get definition (Ctrl+D)")
        self.toanki_button = QPushButton("Add note (Ctrl+S)")
        self.config_button = QPushButton("Configure..")
        self.read_button = QPushButton("Read from clipboard")
    
        self.sentence.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))
        self.sentence.setReadOnly(not (self.settings.value("allow_editing", True, type=bool)))

    def setupWidgets(self):
        self.layout = QGridLayout(self.widget)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 2)
        self.layout.addWidget(QLabel("Anything copied to clipboard will appear here."), 1, 0, 1, 2)
        self.layout.addWidget(self.label_sentence, 2, 0)
        self.layout.addWidget(self.read_button, 2, 1)
        self.layout.addWidget(self.label_word, 4, 0)
        self.layout.addWidget(self.lookup_button, 4, 1)
        self.layout.addWidget(self.label_def, 6, 0, 1, 2)

        self.layout.addWidget(self.sentence, 3, 0, 1, 2)
        self.layout.addWidget(self.word, 5, 0, 1, 2)
        self.layout.addWidget(self.definition, 7, 0, 1, 2)

        self.layout.addWidget(self.toanki_button, 8, 0, 1, 2)
        self.layout.addWidget(self.config_button, 9, 0, 1, 2)

        self.lookup_button.clicked.connect(self.getDefinition)
        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(self.clipboardChanged)

    def initDictionary(self):
        self.parser = WiktionaryParser()

    def configure(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()

    def setupShortcuts(self):
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.createNote)
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.getDefinition)


    def getDefinition(self):
        result = ""
        cursor = self.sentence.textCursor()
        selected = cursor.selectedText().lower()
        cursor2 = self.definition.textCursor()
        selected2 = cursor2.selectedText().lower()
        target = str.strip(selected or selected2 or "")
        if target == "":
            return
        result = self.lookup(target)
        self.word.setText(target)
        self.definition.setText(result)
        cursor.clearSelection()
        self.sentence.setTextCursor(cursor)


        
    
    def setSentence(self, content):
        self.sentence.setText(content)

    def clipboardChanged(self):
        text = QApplication.clipboard().text()
        self.setSentence(text)

    def lookup(self, word):
        print("Looking up: ", word, " in ", self.settings.value("target_language", "english"))
        item = self.parser.fetch(removeAccents(word), self.settings.value("target_language", "english"))
        meanings = []
        for i in item:
            for j in i['definitions']:
                meanings.append("\n".join([str(item[0]) + ". " + item[1] for item in list(enumerate(j['text']))[1:]]))
        return ("\n\n").join(meanings)

    def createNote(self):
        sentence = self.sentence.toPlainText().replace("\n", "<br>")
        word = self.word.text()
        definition = self.definition.toPlainText().replace("\n", "<br>")
        content = {
            "deckName": self.settings.value("deck_name"),
            "modelName": self.settings.value("note_type"),
            "fields": {
                self.settings.value("sentence_field"): sentence,
                self.settings.value("word_field"): word,
                self.settings.value("definition_field"): definition
            }
        }
        print("Sending request with:\n", content)
        
        api = self.settings.value("anki_api")
        try:
            addNote(api, content)
            self.sentence.clear()
            self.word.clear()
            self.definition.clear()
        except Exception as e:
            self.errorNoConnection(e)
            return
        



    def errorNoConnection(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(str(error) + 
            "\nAnkiConnect must be running in order to add notes.\nIf you have AnkiConnect running at an alternative endpoint, be sure to change it in the configuration.")
        msg.exec()

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

