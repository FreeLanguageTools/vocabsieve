import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QTextEdit, QPushButton, QLabel, QLineEdit, QMainWindow, QDialog, QCheckBox, QVBoxLayout
from PyQt6.QtCore import QObject, QTimer, pyqtSlot, QSettings
from wiktionaryparser import WiktionaryParser
from simplesentencemining.config import SettingsDialog
from os import path
from simplesentencemining.tools import addNote

import functools

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
        self.setFixedSize(400, 500)
        self.widget = QWidget()
        self.settings = QSettings("FreeLanguageTools", "SimpleSentenceMining")
        self.initDictionary()
        self.setCentralWidget(self.widget)
        self.initWidgets()
        self.setupWidgets()
        GlobalObject().addEventListener("double clicked", self.getDefinition)
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)
        
    def initWidgets(self):
        self.sentence = MyTextEdit("Sentence here")
        self.sentence.setMinimumHeight(30)
        self.sentence.setMaximumHeight(120)
        self.word = QLineEdit("Word here")
        self.definition = MyTextEdit("Definition here")
        self.definition.setMinimumHeight(70)
        self.definition.setMaximumHeight(400)
        self.label_sentence = QLabel("Sentence")
        self.label_word = QLabel("Word")
        self.label_def = QLabel("Definition")
        self.lookup_button = QPushButton("Get Definition")
        self.toanki_button = QPushButton("Add note")
        self.config_button = QPushButton("Configure..")
    
    def setupWidgets(self):
        self.layout = QGridLayout(self.widget)
        self.layout.addWidget(self.label_sentence, 0, 0, 1, 2)
        self.layout.addWidget(self.label_word, 2, 0, 1, 2)
        self.layout.addWidget(self.label_def, 4, 0, 1, 2)

        self.layout.addWidget(self.sentence, 1, 0, 1, 2)
        self.layout.addWidget(self.word, 3, 0, 1, 2)
        self.layout.addWidget(self.definition, 5, 0, 1, 2)

        self.layout.addWidget(self.lookup_button, 6, 0)
        self.layout.addWidget(self.toanki_button, 6, 1)
        self.layout.addWidget(self.config_button, 7, 0, 1, 2)

        self.lookup_button.clicked.connect(self.getDefinition)
        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)

    def initDictionary(self):
        self.parser = WiktionaryParser()
        #self.parser.set_default_language(self.config['DEFAULT'].get("target_language"))
        #print("Target language is set to: " + self.parser.get_default_language())

    def configure(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()


    def getDefinition(self):
        result = ""
        cursor = self.sentence.textCursor()
        selected = cursor.selectedText().lower()
        cursor2 = self.definition.textCursor()
        selected2 = cursor2.selectedText().lower()
        if selected != "":
            result = self.lookup(selected)
            self.word.setText(selected)
            self.definition.setText(result)
            cursor.clearSelection()
            self.sentence.setTextCursor(cursor)
        elif selected2 != "":
            result = self.lookup(selected2)
            self.definition.setText(result)
            cursor.clearSelection()
            self.sentence.setTextCursor(cursor)
            #cursor2.clearSelection()
        else:
            return
        
    
    def setSentence(self, content):
        self.sentence.setText(content)

    def clipboardChanged(self):
        text = QApplication.clipboard().text()
        self.setSentence(text)

    def lookup(self, word):
        print("Looking up: ", word)
        item = self.parser.fetch(word)
        meanings = []
        for i in item:
            for j in i['definitions']:
                meanings.append("\n".join(j['text'][1:]))
        return word + "\n" + 30*"=" + "\n" + ("\n" + 30*"-" + "\n").join(meanings)

    def createNote(self):
        sentence = self.sentence.toPlainText()
        word = self.word.text()
        definition = self.definition.toPlainText()
        content = {
            "deckName": self.settings.value("deck_name"),
            "modelName": self.settings.value("note_type"),
            "fields": {
                self.settings.value("sentence_field"): sentence,
                self.settings.value("word_field"): word,
                self.settings.value("definition_field"): definition
            }
        }
        addNote(self.settings.value("anki_api"), content)


class MyTextEdit(QTextEdit):
    #def focusOutEvent(self, e):
    #    start = self.selectionStart()
    #    if start == -1:
    #        return
    #    length = self.selectionLength()
    #    super().focusOutEvent(e)
    #    self.setSelection(start, length)
    @pyqtSlot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        GlobalObject().dispatchEvent("double clicked")
        print("Event sent")
        self.textCursor().clearSelection()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DictionaryWindow()

    #keybinder.register_hotkey(w.winId(), "Shift+Ctrl+A", lambda _:print("hello"))
    
    w.show()
    sys.exit(app.exec())

    
    
