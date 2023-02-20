from .GenericImporter import GenericImporter
from .utils import *
from datetime import datetime as dt, timezone as tz
import sqlite3
import os
import re
from PyQt5.QtWidgets import QCheckBox, QLabel
from typing import Tuple, Dict, Set
from ..dictformats import removeprefix
from ..tools import *

def remove_author(titleauthor):
    "Remove author, which is in the last parentheses"
    return re.sub(r'\s*\([^)]*\)$', "", titleauthor)


class KindleVocabImporter(GenericImporter):
    def __init__(self, parent, path):
        super().__init__(parent, "Kindle lookups", path, "kindle")

    def toggleNotesFiltering(self, enable: bool):
        if enable:
            self.notes = self.clippings_items
        else:
            self.notes = None
        self.updateHighlightCount()

    def getNotes(self):
        vocab_db_path = os.path.join(self.path, "system", "vocabulary", "vocab.db")
        clippings_path = os.path.join(self.path, "documents", "My Clippings.txt")

        con = sqlite3.connect(vocab_db_path)
        cur = con.cursor()

        try:
            with open(clippings_path) as file:
                clippings_titleauthors, _, _, clippings_words, _ = zip(*list(grouper(file.read().splitlines(), 5)))
                clippings_words = [re.sub('[\\?\\.!«»…,()\\[\\]]*', "", str(word)).lower() for word in clippings_words]
                clippings_titles = [remove_author(titleauthor.strip("\ufeff")) for titleauthor in clippings_titleauthors]
                self.clippings_items = set(zip(clippings_words, clippings_titles))
                clippings_only = QCheckBox(f"Only select highlighted words ({str(len(clippings_words))} entries found)")
                clippings_only.clicked.connect(self.toggleNotesFiltering)
                self.layout.addRow(clippings_only)
        except Exception as e:
            print(e)
            self.clippings_items = set()
            self.layout.addRow(QLabel("Cannot read highlights. Make sure that your clippings file is in the right place, and its length is a multiple of 5."))


        bookdata = list(cur.execute("SELECT * FROM book_info"))
        bookid2name = dict(zip(list(zip(*bookdata))[2],list(zip(*bookdata))[4]))
        words = []
        booknames = []
        sentences = []
        dates = []
        langcode = self.parent.settings.value("target_language", 'en')
        count = 0
        success_count = 0
        for _, lword, bookid, _, _, sentence, timestamp in cur.execute("SELECT * FROM lookups"):
            if lword.startswith(langcode):
                word = removeprefix(lword, langcode+":")
                count += 1
                success_count += self.parent.rec.recordLookup(word, langcode, True, "kindle", True, timestamp/1000, commit=False) # record everything first
                words.append(word)
                booknames.append(bookid2name[bookid])
                sentences.append(sentence)
                dates.append(str(dt.fromtimestamp(timestamp/1000).astimezone())[:19])
        self.layout.addRow(QLabel("Vocabulary database: " + vocab_db_path))
        self.layout.addRow(QLabel(f"Found {count} lookups in {langcode}, added {success_count} to lookup database."))
        self.parent.rec.conn.commit()
        return words, sentences, dates, booknames