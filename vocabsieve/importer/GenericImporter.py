from PyQt5.QtWidgets import (QDialog, QFormLayout, QLabel, QComboBox, QWidget,
                             QVBoxLayout, QCheckBox, QScrollArea, QPushButton,
                             QProgressBar, QSizePolicy, QApplication)
from PyQt5.QtCore import QDateTime, QCoreApplication
from .BatchNotePreviewer import BatchNotePreviewer
from ..ui.main_window_base import MainWindowBase
from .models import ReadingNote
from ..models import SRSNote
from ..tools import prepareAnkiNoteDict, addNotes, remove_punctuations, canAddNotes

import re
import os
import json
import itertools
from datetime import datetime as dt
from ..global_names import datapath, logger, settings
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..main import MainWindow


def date_to_timestamp(datestr: str):
    return dt.strptime(datestr, "%Y-%m-%d %H:%M:%S").timestamp()


class GenericImporter(QDialog):
    """
    This class implements the UI for extracting highlights.
    Subclass it and override getNotes to have a new importer
    """

    def __init__(self,
                 parent: "MainWindow",
                 src_name: str = "Generic",
                 path: Optional[str] = None,
                 methodname: str = "generic",
                 show_selector_src: bool = True,
                 show_selector_date: bool = True):
        super().__init__(parent)
        self.notes: Optional[set[tuple[str, str]]] = None  # Used for filtering
        self.lang = settings.value('target_language')
        self.methodname = methodname
        self.setWindowTitle(f"Import {src_name}")
        self._parent: MainWindowBase = parent
        self.path = path
        self.setMinimumWidth(500)
        self.src_name = src_name
        self.last_import_books_file = os.path.join(datapath, f"{methodname}_last_import_books.json")
        self._layout = QFormLayout(self)
        self._layout.addRow(QLabel(
            f"<h2>Import {src_name}</h2>"
        ))
        self.reading_notes = self.getNotes()

        self.lookup_button = QPushButton("Look up currently selected")
        self.lookup_button.clicked.connect(self.defineWords)
        self.add_even_if_no_defi = QCheckBox("Add even if no definition found")
        self._layout.addRow(self.add_even_if_no_defi)

        self.orig_dates = [note.date for note in self.reading_notes]
        self.orig_book_names = [note.book_name for note in self.reading_notes]
        self.orig_dates_day = [date[:10] for date in self.orig_dates]
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.notes_count_label = QLabel()
        self._layout.addRow(self.notes_count_label, self.lookup_button)
        self.definition_count_label = QLabel()
        self.anki_button = QPushButton("Add notes to Anki")
        self.anki_button.setEnabled(False)
        self.anki_button.clicked.connect(self.to_anki)
        self.selected_reading_notes: list[ReadingNote] = []
        if show_selector_date:
            possible_start_dates = sorted(set(self.orig_dates_day))
            self.datewidget = QComboBox()
            self._layout.addRow("Use notes starting from: ", self.datewidget)
            self.datewidget.addItems(possible_start_dates)
            try:
                last_import_date = settings.value(f'last_import_date_{self.methodname}', possible_start_dates[0])
                self.datewidget.setCurrentText(max(d for d in possible_start_dates if d <= last_import_date))
            except Exception:
                pass
            self.datewidget.currentTextChanged.connect(self.updateHighlightCount)
        # Source selector, for selecting which books to include
        if show_selector_src:
            self.src_selector = QWidget()
            self.src_checkboxes = []
            self.src_selector._layout = QVBoxLayout(self.src_selector)  # type: ignore
            self._layout.addRow(QLabel("<h3>Select books to extract highlights from</h3>"))
            try:
                with open(self.last_import_books_file, "r", encoding='utf-8') as file:
                    book_names = json.load(file)
            except FileNotFoundError:
                book_names = []
            for book_name in set(self.orig_book_names):
                self.src_checkboxes.append(QCheckBox(book_name))
                if book_name in book_names:
                    self.src_checkboxes[-1].setChecked(True)
                self.src_selector._layout.addWidget(self.src_checkboxes[-1])  # type: ignore
                self.src_checkboxes[-1].clicked.connect(self.updateHighlightCount)
            self.src_selector_scrollarea = QScrollArea()
            self.src_selector_scrollarea.setWidget(self.src_selector)
            self._layout.addRow(self.src_selector_scrollarea)
            self.updateHighlightCount()
        else:
            self.updateHighlightCount(filter_by_notes=False)

        self.preview_widget = BatchNotePreviewer()
        self.preview_widget.setMinimumHeight(300)
        self.preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addRow(QLabel("Preview cards"), self.preview_widget)
        self._layout.addRow(self.progressbar)
        self._layout.addRow(self.definition_count_label, self.anki_button)

    def getNotes(self) -> list[ReadingNote]:
        """
        Returns a tuple of four tuples of equal length
        Respectively, lookup terms (highlights), sentences, dates, and book names
        All the file parsing should happen here.
        dates should be strings to the second, such as "1970-01-01 00:00:00".
        Using T in place of the space is NOT allowed.
        """
        raise NotImplementedError("Should be implemented by subclasses")

    def updateHighlightCount(self, _=False, filter_by_notes: bool = True):
        if filter_by_notes:
            logger.debug("Filtering highlights by book")
            start_date = self.datewidget.currentText()
            selected_book_names = []
            for checkbox in self.src_checkboxes:
                if checkbox.isChecked():
                    logger.debug(f"Selected book: {checkbox.text()}")
                    selected_book_names.append(checkbox.text())
            self.selected_reading_notes = self.filterHighlights(start_date, selected_book_names)
        else:
            self.selected_reading_notes = self.reading_notes
        self.progressbar.setMaximum(len(self.selected_reading_notes))

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
        logger.info(f"Define words triggered on {len(self.selected_reading_notes)} notes")
        self.anki_notes: list[SRSNote] = []
        self.book_names: list[str] = []
        self.lastDate = "1970-01-01 00:00:00"
        defi1 = self._parent.definition
        defi2 = self._parent.definition2
        definition2_enabled = settings.value("sg2_enabled", False, type=bool)

        # No using any of these buttons to prevent race conditions
        self.lookup_button.setEnabled(False)
        self.anki_button.setEnabled(False)
        self.preview_widget.reset()
        count = 0
        for n_looked_up, note in enumerate(self.selected_reading_notes):
            QCoreApplication.processEvents()
            logger.debug(f"Handling reading note: {note}")
            self.lastDate = max(note.date, self.lastDate)
            # Remove punctuations
            word = remove_punctuations(note.lookup_term)
            if settings.value("bold_word", True, type=bool):
                sentence = note.sentence.replace(word, f"<strong>{word}</strong>")
            else:
                sentence = note.sentence

            definition1 = defi1.getFirstDefinition(word)
            if definition2_enabled:
                definition2 = defi2.getFirstDefinition(word)
            else:
                definition2 = None
            if not (definition1 or definition2) and not self.add_even_if_no_defi.isChecked():
                continue
            count += 1
            self.definition_count_label.setText(
                str(count) + " notes will be sent")
            QCoreApplication.processEvents()

            audio_path = ""
            if json.loads(settings.value("audio_sg", "[]")) != []:
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
            if settings.value("tags", "vocabsieve").strip():
                tags.extend(settings.value("tags", "vocabsieve").strip().split())
            tags.append(self.methodname)
            tags.append(note.book_name.replace(" ", "_"))

            # replace word with headword if it exists
            if definition1 is not None:
                word = definition1.headword
            elif definition2 is not None:
                word = definition2.headword

            new_note_item = SRSNote(
                word=word,  # fine if no definition
                sentence=sentence,  # fine if empty string
                definition1=self._parent.definition.toAnki(definition1) if definition1 is not None else None,
                definition2=self._parent.definition2.toAnki(definition2) if definition2 is not None else None,
                audio_path=audio_path or None,
                tags=tags
            )
            self.preview_widget.appendNoteItem(new_note_item)
            self.anki_notes.append(new_note_item)
            self.progressbar.setValue(n_looked_up + 1)
        self.progressbar.setValue(len(self.selected_reading_notes))

        # Unlock buttons again now
        self.lookup_button.setEnabled(True)
        self.anki_button.setEnabled(True)

    def to_anki(self):
        notes_data = []
        for note in self.anki_notes:
            notes_data.append(
                prepareAnkiNoteDict(self._parent.getAnkiSettings(), note)
            )

        # Check if we can add notes
        logger.info(f"Trying to add {len(notes_data)} notes to Anki.")
        checks = canAddNotes(settings.value("anki_api"), notes_data)
        logger.info(f"{sum(checks)} out of {len(checks)} notes can be added to Anki, proceeding.")
        # Filter out the notes that can't be added
        notes_data = list(itertools.compress(notes_data, checks))

        res = addNotes(settings.value("anki_api"), notes_data)
        # Record last import data
        if self.methodname != "auto":  # don't save for auto vocab extraction
            settings.setValue("last_import_method", self.methodname)
            settings.setValue("last_import_path", self.path)
            settings.setValue(f"last_import_date_{self.methodname}", self.lastDate[:10])
            with open(self.last_import_books_file, "w", encoding='utf-8') as file:
                json.dump([cb.text() for cb in self.src_checkboxes if cb.isChecked()], file)

        self._layout.addRow(QLabel(
            QDateTime.currentDateTime().toString('[hh:mm:ss]') + " "
            + str(len(notes_data))
            + " notes have been exported, of which "
            + str(len([i for i in res if i]))
            + " were successfully added to your collection."))
