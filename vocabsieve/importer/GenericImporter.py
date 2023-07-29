from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qt import *
import re
import json
from vocabsieve.tools import addNotes
from vocabsieve.dictionary import getAudio
from datetime import datetime as dt
from itertools import compress

from .utils import *
from .BatchNotePreviewer import BatchNotePreviewer

def date_to_timestamp(datestr: str):
    return dt.strptime(datestr, "%Y-%m-%d %H:%M:%S").timestamp()

class GenericImporter(QDialog):
    """
    This class implements the UI for extracting highlights.
    Subclass it and override getNotes to have a new importer
    """
    def __init__(self, parent, src_name="Generic", path=None, methodname="generic"):
        super().__init__(parent)
        self.settings = parent.settings
        self.notes = None # Used for filtering
        self.lang = parent.settings.value('target_language')
        self.methodname = methodname
        self.setWindowTitle(f"Import {src_name}")
        self.parent = parent
        self.path = path
        self.selected_highlight_items = []
        self.setMinimumWidth(500)
        self.src_name = src_name
        self.layout = QFormLayout(self)
        self.layout.addRow(QLabel(
            f"<h2>Import {src_name}</h2>"
        ))
        self.orig_lookup_terms, self.orig_sentences, self.orig_dates, self.orig_book_names = self.getNotes()
        self.orig_dates_day = [date[:10] for date in self.orig_dates]
        possible_start_dates = sorted(set(self.orig_dates_day))
        self.datewidget = QComboBox()
        self.datewidget.addItems(possible_start_dates)
        self.datewidget.currentTextChanged.connect(self.updateHighlightCount)
        # Source selector, for selecting which books to include
        self.src_selector = QWidget()
        self.src_checkboxes = []
        self.src_selector.layout = QVBoxLayout(self.src_selector)
        self.layout.addRow(QLabel("<h3>Select books to extract highlights from</h3>"))

        self.lookup_button = QPushButton("Look up currently selected")
        self.lookup_button.clicked.connect(self.defineWords)
        self.lookup_button.setEnabled(False)
    
        for book_name in set(self.orig_book_names):
            self.src_checkboxes.append(
                QCheckBox(truncate_middle(book_name, 90)))
            self.src_selector.layout.addWidget(self.src_checkboxes[-1])
            self.src_checkboxes[-1].clicked.connect(self.updateHighlightCount)
        
        self.src_selector_scrollarea = QScrollArea()
        self.src_selector_scrollarea.setWidget(self.src_selector)
        self.layout.addRow(self.src_selector_scrollarea)
        self.layout.addRow("Use notes starting from: ", self.datewidget)
        self.notes_count_label = QLabel()
        self.layout.addRow(self.notes_count_label, self.lookup_button)
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.definition_count_label = QLabel()
        self.anki_button = QPushButton("Add notes to Anki")
        self.anki_button.setEnabled(False)
        self.anki_button.clicked.connect(self.to_anki)

        self.preview_widget = BatchNotePreviewer()
        self.preview_widget.setMinimumHeight(300)
        self.preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addRow(QLabel("Preview cards"), self.preview_widget)
        self.layout.addRow(self.progressbar)
        self.layout.addRow(self.definition_count_label, self.anki_button)
        try:
            last_import_date = self.parent.settings.value(f'last_import_date_{self.methodname}', possible_start_dates[0])
            self.datewidget.setCurrentText(max(d for d in possible_start_dates if d <= last_import_date))
        except Exception:
            pass



    def getNotes(self):
        """
        Returns a tuple of four tuples of equal length
        Respectively, lookup terms (highlights), sentences, dates, and book names
        All the file parsing should happen here.
        dates should be strings to the second, such as "1970-01-01 00:00:00".
        Using T in place of the space is NOT allowed.
        """
        return ((), (), (), ())

    def updateHighlightCount(self):
        start_date = self.datewidget.currentText()
        selected_book_names = []
        for checkbox in self.src_checkboxes:
            if checkbox.isChecked():
                selected_book_names.append(checkbox.text())
        self.selected_highlight_items = self.filterHighlights(start_date, selected_book_names, self.notes)
        if self.selected_highlight_items:
            self.lookup_button.setEnabled(True)
            self.progressbar.setMaximum(len(self.selected_highlight_items)) 
        else:
            self.lookup_button.setEnabled(False)
        self.progressbar.setValue(0)
        self.notes_count_label.setText(f"{len(self.selected_highlight_items)} highlights selected")

    def filterHighlights(self, start_date, book_names, notes=None):
        try:
            lookup_terms, sentences, dates, book_names = zip(*compress(
                zip(self.orig_lookup_terms, self.orig_sentences, self.orig_dates, self.orig_book_names), 
                map(lambda w, b, d: (d[:10] >= start_date and b in book_names) and ((w.lower(),b) in notes if notes else True), self.orig_lookup_terms, self.orig_book_names, self.orig_dates)
                ))
        except ValueError:
            lookup_terms, sentences, dates, book_names = [],[],[],[]
        return list(zip(lookup_terms, sentences, dates, book_names))


    def defineWords(self):
        self.sentences = []
        self.words = []
        self.definitions = []
        self.definition2s = []
        self.audio_paths = []
        self.book_names = []
        self.lastDate = "1970-01-01 00:00:00"

        # No using any of these buttons to prevent race conditions
        self.lookup_button.setEnabled(False)
        self.anki_button.setEnabled(False)
        self.preview_widget.reset()
        count = 0
        for n_looked_up, (lookup_term, sentence, date, book_name) in enumerate(self.selected_highlight_items):
            # Remove punctuations
            self.lastDate = date
            word = re.sub('[\\?\\.!«»…,()\\[\\]]*', "", lookup_term)
            if sentence:
                if self.settings.value("bold_word", True, type=bool):
                    self.sentences.append(sentence.replace("_", "").replace(word, f"__{word}__"))
                    
                else:
                    self.sentences.append(sentence)
                item = self.parent.lookup(word, True)
                if not item['definition'].startswith("<b>Definition for"):
                    count += 1
                    self.words.append(item['word'])
                    self.definitions.append(item['definition'])
                    self.definition_count_label.setText(
                        str(count) + " definitions found")
                    self.definition2s.append(item.get('definition2', ""))
                    self.preview_widget.appendNoteItem(sentence, item, word)
                    QApplication.processEvents()
                else:
                    self.words.append(word)
                    self.definitions.append("")
                    self.definition2s.append("")

                audio_path = ""
                if self.settings.value("audio_dict", "Forvo (all)") != "<disabled>":
                    try:
                        audios = getAudio(
                                word,
                                self.settings.value("target_language", 'en'),
                                dictionary=self.settings.value("audio_dict", "Forvo (all)"),
                                custom_dicts=json.loads(
                                    self.settings.value("custom_dicts", '[]')))
                    except Exception:
                        audios = {}
                    if audios:
                        # First item
                        audio_path = audios[next(iter(audios))]
                self.audio_paths.append(audio_path)
                self.book_names.append(book_name)
            else:
                print("no sentence")
                #self.sentences.append("")
                #self.definitions.append("")
                #self.words.append("")
                #self.definition2s.append("")
                #self.audio_paths.append("")
            self.progressbar.setValue(n_looked_up+1)
            
        
        # Unlock buttons again now
        self.lookup_button.setEnabled(True)
        self.anki_button.setEnabled(True)
        print("Lengths", len(self.sentences), len(self.words), len(self.definitions), len(self.audio_paths))
    def to_anki(self):
        notes = []
        for word, sentence, definition, definition2, audio_path, book_name in zip(
                self.words, self.sentences, self.definitions, self.definition2s, self.audio_paths, self.book_names):
            if word and sentence and definition:
                if self.settings.value("bold_word", 1, type=int):
                    sentence = re.sub(
                        r"__(.+?)__",
                        r"<strong>\1</strong>",
                        sentence
                        )
                tags = " ".join([
                    self.parent.settings.value("tags", "vocabsieve").strip(),
                    self.methodname,
                    book_name.replace(" ","_")
                    ]
                    )
                content = {
                    "deckName": self.parent.settings.value("deck_name"),
                    "modelName": self.parent.settings.value("note_type"),
                    "fields": {
                        self.parent.settings.value("sentence_field"): sentence,
                        self.parent.settings.value("word_field"): word,
                    },
                    "tags": tags.split(" ")
                }
                definition = definition.replace("\n", "<br>")
                content['fields'][self.parent.settings.value(
                    'definition_field')] = definition
                if self.settings.value("dict_source2", "<disabled>") != '<disabled>':
                    definition2 = definition2.replace("\n", "<br>")
                    content['fields'][self.parent.settings.value('definition2_field')] = definition2
                if self.settings.value("audio_dict", "<disabled>") != '<disabled>' and audio_path:
                    content['audio'] = {}
                    if audio_path.startswith("https://") or audio_path.startswith("http://"):
                        content['audio']['url'] = audio_path
                    else:
                        content['audio']['path'] = audio_path
                    content['audio']['filename'] = audio_path.replace("\\", "/").split("/")[-1]
                    content['audio']['fields'] = [self.settings.value('pronunciation_field')]

                notes.append(content)
        res = addNotes(self.parent.settings.value("anki_api"), notes)
        # Record last import data
        if self.methodname != "auto": # don't save for auto vocab extraction
            self.parent.settings.setValue("last_import_method", self.methodname)
            self.parent.settings.setValue("last_import_path", self.path)
            self.parent.settings.setValue(f"last_import_date_{self.methodname}", self.lastDate[:10])

        self.layout.addRow(QLabel(
            QDateTime.currentDateTime().toString('[hh:mm:ss]') + " "
            + str(len(notes)) 
            + " notes have been exported, of which " 
            + str(len([i for i in res if i]))
            + " were successfully added to your collection."))