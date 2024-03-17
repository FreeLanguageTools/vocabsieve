import os
import sqlite3
from datetime import datetime as dt
from PyQt5.QtWidgets import QLabel
from slpp import slpp
from typing import TYPE_CHECKING
from .GenericImporter import GenericImporter
from .utils import koreader_scandir, findDBpath, findHistoryPath
from .models import ReadingNote
from ..models import LookupRecord
from ..global_names import settings, logger
from ..ui.main_window_base import MainWindowBase
import time

if TYPE_CHECKING:
    from ..main import MainWindow


def getBookMetadata(path):
    _, ext = os.path.splitext(path)
    notepath = os.path.join(path.removesuffix(ext) + ".sdr", f"metadata{ext}.lua")

    with open(notepath, encoding='utf8') as f:
        data = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))
        try:
            booklang = data['doc_props']['language']  # type: ignore
            booktitle = data['doc_props']['title']  # type: ignore
        except TypeError:
            booklang = settings.value("target_language", "en")
            booktitle = os.path.basename(path).removesuffix(ext)
        except KeyError:
            booklang = settings.value("target_language", "en")
            booktitle = os.path.basename(path).removesuffix(ext)
    return booklang, booktitle


class KoreaderVocabImporter(GenericImporter):
    def __init__(self, parent: "MainWindow", path):
        self.splitter = parent.splitter
        super().__init__(parent, "KOReader vocab builder", path, "koreader-vocab")

    def getNotes(self):
        bookfiles = koreader_scandir(self.path)
        langcode = settings.value("target_language", "en")
        metadata = []
        for bookfile in bookfiles:
            metadata.append(getBookMetadata(bookfile))

        books_in_lang = [book[1] for book in metadata if book[0].startswith(langcode)]
        logger.debug(f"Books in language {langcode}: {books_in_lang}")
        logger.debug(
            f"Other books have been skipped. They are {', '.join([book[1] for book in metadata if not book[0].startswith(langcode)])}")
        self.dbpath = findDBpath(self.path)
        logger.debug("KOReader vocab db path: " + self.dbpath)
        con = sqlite3.connect(self.dbpath)
        cur = con.cursor()
        count = 0

        bookmap = {}

        for bookid, bookname in cur.execute("SELECT id, name FROM title"):
            if bookname in books_in_lang:
                bookmap[bookid] = bookname

        reading_notes = []
        for timestamp, word, title_id, prev_context, next_context in cur.execute(
                "SELECT create_time, word, title_id, prev_context, next_context FROM vocabulary"):
            if title_id in bookmap:
                if prev_context and next_context:
                    ctx = prev_context.strip() + f" {word} " + next_context.strip()  # ensure space before and after
                else:
                    continue
                sentence = ""
                for sentence_ in self.splitter.split(ctx):
                    if word in sentence_:
                        sentence = sentence_
                if sentence:
                    count += 1
                    #items.append((word, sentence, str(dt.fromtimestamp(timestamp).astimezone())[:19], bookmap[title_id]))
                    reading_notes.append(
                        ReadingNote(
                            lookup_term=word,
                            sentence=sentence,
                            book_name=bookmap[title_id],
                            date=str(dt.fromtimestamp(timestamp).astimezone())[:19]
                        )
                    )

        self._layout.addRow(QLabel("Vocabulary database: " + self.dbpath))
        self._layout.addRow(QLabel(f"Found {count} notes in Vocabulary Builder in language '{langcode}'"))

        try:
            self.histpath = findHistoryPath(self.path)
            logger.debug("KOReader history path: " + self.histpath)
            d = []
            with open(self.histpath, encoding="utf-8") as f:
                content = f.read().split("LookupHistoryEntry")[1:]
                for item in content:
                    d.append(slpp.decode(item))
        except Exception as e:
            logger.error("Failed to find or open lookup_history.lua. Lookups will not be tracked this time.")
            logger.error(e)
            logger.error("Make sure that it is located somewhere under the selected KOReader directory.")
            self._layout.addRow(
                QLabel("Failed to find/read lookup_history.lua. Lookups will not be tracked this time."))
        else:
            entries = [entry['data'].get(next(iter(entry['data']))) for entry in d]
            entries = [(entry['word'], entry['book_title'], entry['time']) for entry in entries]
            count = 0
            lookups_count_before = self._parent.rec.countLookups(langcode)
            for word, booktitle, timestamp in entries:
                if booktitle in books_in_lang:
                    count += 1
                    self._parent.rec.recordLookup(
                        LookupRecord(
                            word=word,
                            language=langcode,
                            source="koreader"
                        ),
                        timestamp,
                        commit=False
                    )
            self._parent.rec.conn.commit()
            lookups_count_after = self._parent.rec.countLookups(langcode)
            self._layout.addRow(QLabel("Lookup history: " + self.histpath))
            self._layout.addRow(
                QLabel(f"Found {count} lookups in {langcode}, added { lookups_count_after - lookups_count_before } to lookup database."))

        return reading_notes
