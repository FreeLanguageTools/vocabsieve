import os
import sqlite3
from datetime import datetime as dt
from datetime import timezone as tz
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from slpp import slpp

from .GenericImporter import GenericImporter
from .utils import *
from ..tools import *



def getBookMetadata(path):
    basename, ext = os.path.splitext(path)
    notepath = os.path.join(removesuffix(path, ext) + ".sdr", f"metadata{ext}.lua")
            
    with open(notepath, encoding='utf8') as f:
        data = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))
        booklang = data['doc_props']['language']
        booktitle = data['doc_props']['title']
    return booklang, booktitle


class KoreaderVocabImporter(GenericImporter):
    def __init__(self, parent, path):
        super().__init__(parent, "KOReader vocab builder", path, "koreader-vocab")

    def getNotes(self):
        bookfiles = koreader_scandir(self.path)
        langcode = self.parent.settings.value("target_language", "en")
        metadata = []
        for bookfile in bookfiles:
            metadata.append(getBookMetadata(bookfile))

        books_in_lang = [book[1] for book in metadata if book[0] == langcode]
        self.dbpath = findDBpath(self.path)
        con = sqlite3.connect(self.dbpath)
        cur = con.cursor()
        bookids = []
        count = 0
        success_count = 0

        bookmap = {}

        for bookid, bookname in cur.execute("SELECT id, name FROM title"):
            if bookname in books_in_lang:
                bookmap[bookid] = bookname

        items = []
        for timestamp, word, title_id, prev_context, next_context in cur.execute("SELECT create_time, word, title_id, prev_context, next_context FROM vocabulary"):
            #print(word, title_id)
            if title_id in bookmap:
                if prev_context and next_context:
                    ctx = prev_context + word + next_context
                else:
                    continue
                sentence = ""
                for sentence_ in split_to_sentences(ctx, language=langcode):
                    if word in sentence_:
                        sentence = sentence_
                if sentence:
                    count += 1
                    items.append((word, sentence, str(dt.fromtimestamp(timestamp).astimezone())[:19], bookmap[title_id]))

        self.layout.addRow(QLabel("Vocabulary database: " + self.dbpath))
        self.layout.addRow(QLabel(f"Found {count} notes in Vocabulary Builder in language '{langcode}'"))
        
        try:
            self.histpath = findHistoryPath(self.path)
            d = []
            with open(self.histpath) as f:
                with open(self.histpath) as f:
                    content = f.read().split("LookupHistoryEntry")[1:]
                    for item in content:
                        d.append(slpp.decode(item))
            entries = [entry['data'].get(next(iter(entry['data']))) for entry in d]
            entries = [(entry['word'], entry['book_title'], entry['time']) for entry in entries]
            count = 0
            success_count = 0
            for word, booktitle, timestamp in entries:
                if booktitle in books_in_lang:
                    count += 1
                    success_count += self.parent.rec.recordLookup(word, langcode, True, "koreader", True, timestamp, commit=False)
            self.parent.rec.conn.commit()

            self.layout.addRow(QLabel("Lookup history: " + self.histpath))
            self.layout.addRow(QLabel(f"Found {count} lookups in {langcode}, added {success_count} to lookup database."))
        except Exception as e:
            print(e)
            self.layout.addRow(QLabel("Failed to find/read lookup_history.lua. Lookups will not be tracked this time."))

        return zip(*items)
