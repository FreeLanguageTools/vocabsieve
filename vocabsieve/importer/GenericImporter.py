from PyQt5.QtWidgets import (QDialog, QFormLayout, QLabel, QComboBox, QWidget, 
                             QVBoxLayout, QCheckBox, QScrollArea, QPushButton, 
                             QProgressBar, QSizePolicy, QApplication)
from PyQt5.QtCore import QDateTime
from .BatchNotePreviewer import BatchNotePreviewer
from ..ui.main_window_base import MainWindowBase
from .models import ReadingNote
from ..models import SRSNote
from ..tools import prepareAnkiNoteDict
from .utils import truncate_middle

import re
import json

from vocabsieve.tools import addNotes
from datetime import datetime as dt
from .BatchNotePreviewer import BatchNotePreviewer
from ..ui.main_window_base import MainWindowBase
from .models import ReadingNote
from ..models import SRSNote
from ..tools import prepareAnkiNoteDict
from typing import Optional

def date_to_timestamp(datestr: str):
    return dt.strptime(datestr, "%Y-%m-%d %H:%M:%S").timestamp()

class GenericImporter(QDialog):
    """
    This class implements the UI for extracting highlights.
    Subclass it and override getNotes to have a new importer
    """
    def __init__(self, parent: MainWindowBase, src_name: str = "Generic", path: Optional[str] = None, methodname: str ="generic"):
        super().__init__(parent)
        self.settings = parent.settings
        self.notes: Optional[set[tuple[str, str]]] = None # Used for filtering
        self.lang = parent.settings.value('target_language')
        self.methodname = methodname
        self.setWindowTitle(f"Import {src_name}")
        self._parent: MainWindowBase = parent
        self.path = path
        self.setMinimumWidth(500)
        self.src_name = src_name
        self._layout = QFormLayout(self)
        self._layout.addRow(QLabel(
            f"<h2>Import {src_name}</h2>"
        ))
        self.reading_notes = self.getNotes()
        self.selected_reading_notes = self.reading_notes


        self.orig_dates = [note.date for note in self.reading_notes]
        self.orig_book_names = [note.book_name for note in self.reading_notes]
        self.orig_dates_day = [date[:10] for date in self.orig_dates]
        possible_start_dates = sorted(set(self.orig_dates_day))
        self.datewidget = QComboBox()
        self.datewidget.addItems(possible_start_dates)
        self.datewidget.currentTextChanged.connect(self.updateHighlightCount)
        # Source selector, for selecting which books to include
        self.src_selector = QWidget()
        self.src_checkboxes = []
        self.src_selector._layout = QVBoxLayout(self.src_selector) # type: ignore
        self._layout.addRow(QLabel("<h3>Select books to extract highlights from</h3>"))

        self.lookup_button = QPushButton("Look up currently selected")
        self.lookup_button.clicked.connect(self.defineWords)
        self.lookup_button.setEnabled(False)
    
        for book_name in set(self.orig_book_names):
            self.src_checkboxes.append(
                QCheckBox(truncate_middle(book_name, 90)))
            self.src_selector._layout.addWidget(self.src_checkboxes[-1]) # type: ignore
            self.src_checkboxes[-1].clicked.connect(self.updateHighlightCount)
        
        self.src_selector_scrollarea = QScrollArea()
        self.src_selector_scrollarea.setWidget(self.src_selector)
        self._layout.addRow(self.src_selector_scrollarea)
        self._layout.addRow("Use notes starting from: ", self.datewidget)
        self.notes_count_label = QLabel()
        self._layout.addRow(self.notes_count_label, self.lookup_button)
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.definition_count_label = QLabel()
        self.anki_button = QPushButton("Add notes to Anki")
        self.anki_button.setEnabled(False)
        self.anki_button.clicked.connect(self.to_anki)

        self.preview_widget = BatchNotePreviewer()
        self.preview_widget.setMinimumHeight(300)
        self.preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addRow(QLabel("Preview cards"), self.preview_widget)
        self._layout.addRow(self.progressbar)
        self._layout.addRow(self.definition_count_label, self.anki_button)
        try:
            last_import_date = self._parent.settings.value(f'last_import_date_{self.methodname}', possible_start_dates[0])
            self.datewidget.setCurrentText(max(d for d in possible_start_dates if d <= last_import_date))
        except Exception:
            pass



    def getNotes(self) -> list[ReadingNote]:
        """
        Returns a tuple of four tuples of equal length
        Respectively, lookup terms (highlights), sentences, dates, and book names
        All the file parsing should happen here.
        dates should be strings to the second, such as "1970-01-01 00:00:00".
        Using T in place of the space is NOT allowed.
        """
        raise NotImplementedError("Should be implemented by subclasses")

    def updateHighlightCount(self):
        start_date = self.datewidget.currentText()
        selected_book_names = []
        for checkbox in self.src_checkboxes:
            if checkbox.isChecked():
                selected_book_names.append(checkbox.text())
        self.selected_reading_notes = self.filterHighlights(start_date, selected_book_names)
        if self.selected_reading_notes:
            self.lookup_button.setEnabled(True)
            self.progressbar.setMaximum(len(self.selected_reading_notes)) 
        else:
            self.lookup_button.setEnabled(False)
        self.progressbar.setValue(0)
        self.notes_count_label.setText(f"{len(self.selected_reading_notes)} highlights selected")

    def filterHighlights(self, start_date, book_names) -> list[ReadingNote]:
        new_reading_notes = []
        for item in self.reading_notes:
            if item.date[:10] >= start_date and item.book_name in book_names:
                if self.notes:
                    if (item.lookup_term.lower(), item.book_name) in self.notes:
                        new_reading_notes.append(item)
                else:
                    new_reading_notes.append(item)

                

        return new_reading_notes



    def defineWords(self) -> None:
        add_even_if_no_definition = self.settings.value("add_even_if_no_definition", False, type=bool)
        self.anki_notes: list[SRSNote] = []
        self.book_names: list[str] = []
        self.lastDate = "1970-01-01 00:00:00"
        defi1 = self._parent.definition
        defi2 = self._parent.definition2
        definition2_enabled = self.settings.value("sg2_enabled", False, type=bool)

        # No using any of these buttons to prevent race conditions
        self.lookup_button.setEnabled(False)
        self.anki_button.setEnabled(False)
        self.preview_widget.reset()
        count = 0
        for n_looked_up, note in enumerate(self.selected_reading_notes):
            # Remove punctuations
            self.lastDate = note.date
            word = re.sub('[\\?\\.!«»…,()\\[\\]]*', "", note.lookup_term)
            if note.sentence:
                if self.settings.value("bold_word", True, type=bool):
                    sentence = note.sentence.replace("_", "").replace(word, f"<strong>{word}</strong>")
                else:
                    sentence = note.sentence
                    
                if defi1.getDefinitions(word):
                    definition1 = defi1.getDefinitions(word)[0]
                else:
                    definition1 = None
                if definition2_enabled:
                    if defi2.getDefinitions(word):
                        definition2 = defi2.getDefinitions(word)[0]
                    else:
                        definition2 = None
                else:
                    definition2 = None
                if definition1 is None:
                    continue # TODO implement a way to add words without definition1
                count += 1
                self.definition_count_label.setText(
                    str(count) + " definitions found")
                QApplication.processEvents()

                audio_path = ""
                if json.loads(self.settings.value("audio_sg", "[]")) != []:
                    try:
                        audio_definitions = self._parent.audio_selector.getDefinitions(word)
                        if audio_definitions and audio_definitions[0].audios is not None:
                            audios = audio_definitions[0].audios
                        else:
                            audios = {}
                    except Exception:
                        audios = {}
                    if audios:
                        # First item
                        audio_path = audios[next(iter(audios))]

                tags = []
                if self.settings.value("tags", "vocabsieve").strip():
                    tags.extend(self.settings.value("tags", "vocabsieve").strip().split())
                tags.append(self.methodname)
                tags.append(note.book_name.replace(" ","_"))
                
                new_note_item = SRSNote(
                        word=definition1.headword,
                        sentence=sentence,
                        definition1=definition1.definition,
                        definition2=definition2.definition if definition2 else None,
                        audio_path=audio_path,
                        tags=tags
                        )
                self.preview_widget.appendNoteItem(new_note_item)
                self.anki_notes.append(new_note_item)
            self.progressbar.setValue(n_looked_up+1)
        
        # Unlock buttons again now
        self.lookup_button.setEnabled(True)
        self.anki_button.setEnabled(True)
    def to_anki(self):
        notes_data = []
        for note in self.anki_notes:
            notes_data.append(
                prepareAnkiNoteDict(self._parent.getAnkiSettings(), note)
                )

        res = addNotes(self._parent.settings.value("anki_api"), notes_data)
        # Record last import data
        if self.methodname != "auto": # don't save for auto vocab extraction
            self._parent.settings.setValue("last_import_method", self.methodname)
            self._parent.settings.setValue("last_import_path", self.path)
            self._parent.settings.setValue(f"last_import_date_{self.methodname}", self.lastDate[:10])

        self._layout.addRow(QLabel(
            QDateTime.currentDateTime().toString('[hh:mm:ss]') + " "
            + str(len(notes_data)) 
            + " notes have been exported, of which " 
            + str(len([i for i in res if i]))
            + " were successfully added to your collection."))