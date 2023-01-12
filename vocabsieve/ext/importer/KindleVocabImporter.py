from .GenericImporter import GenericImporter
from .utils import *
from datetime import datetime as dt, timezone as tz
import sqlite3
from ...dictformats import removeprefix

class KindleVocabImporter(GenericImporter):
    def __init__(self, parent, path):
        super().__init__(parent, "Kindle vocab.db lookups", path, "kindle_vocabdb")

    def getNotes(self):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        bookdata = list(cur.execute("SELECT * FROM book_info"))
        bookid2name = dict(zip(list(zip(*bookdata))[2],list(zip(*bookdata))[4]))
        words = []
        booknames = []
        sentences = []
        dates = []
        langcode = self.parent.settings.value("target_language", 'en')
        for _, lword, bookid, _, _, sentence, timestamp in cur.execute("SELECT * FROM lookups"):
            if lword.startswith(langcode):
                words.append(removeprefix(lword, langcode+":"))
                booknames.append(bookid2name[bookid])
                sentences.append(sentence)
                dates.append(str(dt.fromtimestamp(timestamp/1000).replace(tzinfo=tz.utc).astimezone())[:19])
        return words, sentences, dates, booknames